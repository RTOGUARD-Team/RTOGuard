import { useState } from "react";
import RiskBadge from "./RiskBadge";
import { scoreOrder } from "../services/api";

function SimulationCard() {
  const [formData, setFormData] = useState({
    customer_id: "1",
    order_value: "1400",
    payment_mode: "COD",
    pincode: "411001",
    category: "Apparel",
    is_festive_window: false,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const calculateRisk = async () => {
    if (!formData.order_value || Number(formData.order_value) <= 0) {
      setError("Please enter a valid order value.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Connect to Enterprise ML Risk Engine & Cost Calculator via Backend API
      const evaluatedDecision = await scoreOrder({
        order_id: `SIM-${Date.now().toString().slice(-6)}`,
        customer_id: formData.customer_id.trim() || "1",
        order_value: Number(formData.order_value),
        payment_mode: formData.payment_mode,
        pincode: formData.pincode.trim() || "110001",
        category: formData.category,
        is_festive_window: Boolean(formData.is_festive_window),
      });

      setResult(evaluatedDecision);
    } catch (err) {
      console.error("Simulation error:", err);
      setError(err.message || "Failed to score order. Ensure backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="simulation-card">
      <div className="simulation-grid">
        <div className="simulation-form">
          <label>
            Customer ID (Lookup / History)
            <input
              type="text"
              name="customer_id"
              placeholder="e.g. 1, 101, or CUS-1001"
              value={formData.customer_id}
              onChange={handleChange}
            />
          </label>

          <label>
            Order Value (₹)
            <input
              type="number"
              name="order_value"
              placeholder="e.g. 2500"
              value={formData.order_value}
              onChange={handleChange}
            />
          </label>

          <label>
            Payment Mode
            <select
              name="payment_mode"
              value={formData.payment_mode}
              onChange={handleChange}
            >
              <option value="COD">Cash on Delivery (COD)</option>
              <option value="PREPAID">Prepaid</option>
            </select>
          </label>

          <label>
            Delivery Pincode
            <input
              type="text"
              name="pincode"
              placeholder="e.g. 411001"
              value={formData.pincode}
              onChange={handleChange}
            />
          </label>

          <label>
            Product Category
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
            >
              <option value="Apparel">Apparel</option>
              <option value="Electronics">Electronics</option>
              <option value="Fashion">Fashion</option>
              <option value="Home & Kitchen">Home & Kitchen</option>
            </select>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              name="is_festive_window"
              checked={formData.is_festive_window}
              onChange={handleChange}
            />
            Festive Window Multiplier
          </label>

          {error && <div style={{ color: "#ef4444", fontSize: "0.875rem", marginTop: "0.5rem" }}>{error}</div>}

          <button
            className="simulate-button"
            onClick={calculateRisk}
            disabled={loading}
          >
            {loading ? "Analyzing Models..." : "Analyze Risk (Enterprise Engine)"}
          </button>
        </div>

        <div className="simulation-result">
          {!result ? (
            <div className="empty-result">
              <h3>Risk Result</h3>
              <p>
                Enter order details and click
                <strong> Analyze Risk </strong>
                to run live ML inference.
              </p>
            </div>
          ) : (
            <>
              <div className="result-header">
                <div>
                  <span>Predicted Risk Score</span>
                  <strong style={{ fontSize: "1.75rem", display: "block", color: "#111827" }}>
                    {Math.round(result.risk_score * 100)}%
                  </strong>
                  <small style={{ color: "#6b7280" }}>
                    Status: <strong>{result.customer_status?.toUpperCase() || "EVALUATED"}</strong>
                  </small>
                </div>

                <RiskBadge level={result.risk_level} />
              </div>

              <div className="result-section">
                <h3>Risk Driving Factors (ML Explainability)</h3>
                {result.top_factors && result.top_factors.length > 0 ? (
                  <ul className="reason-list">
                    {result.top_factors.map((factor, index) => (
                      <li key={index}>{factor}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No adverse risk signals detected.</p>
                )}
              </div>

              <div className="result-section">
                <h3>Store Manager Recommendation</h3>
                <div className="recommendation" style={{ fontWeight: 600, padding: "0.75rem 1rem", backgroundColor: "#f3f4f6", borderRadius: "8px", borderLeft: "4px solid #3b82f6" }}>
                  {result.recommended_action}
                  {result.suggested_deposit > 0 && (
                    <div style={{ marginTop: "4px", fontSize: "0.85rem", color: "#4b5563" }}>
                      Suggested Advance Deposit: <strong>₹{result.suggested_deposit}</strong>
                    </div>
                  )}
                </div>
              </div>

              <div className="result-section" style={{ borderTop: "1px solid #e5e7eb", paddingTop: "0.75rem", marginTop: "0.75rem" }}>
                <h3>Economic Impact Assessment</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.875rem" }}>
                  <div>
                    <span style={{ color: "#6b7280" }}>Expected Baseline Loss:</span>
                    <strong style={{ display: "block" }}>₹{result.baseline_expected_rto_loss?.toFixed(2) || "0.00"}</strong>
                  </div>
                  <div>
                    <span style={{ color: "#6b7280" }}>Net Loss Avoided:</span>
                    <strong style={{ display: "block", color: result.net_impact > 0 ? "#10b981" : "#374151" }}>
                      ₹{result.net_impact?.toFixed(2) || "0.00"}
                    </strong>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

export default SimulationCard;