import { useState } from "react";
import RiskBadge from "./RiskBadge";

function SimulationCard() {
  const [formData, setFormData] = useState({
    order_value: "",
    payment_mode: "COD",
    pincode: "",
    category: "Apparel",
    is_festive_window: false,
  });

  const [result, setResult] = useState(null);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const calculateRisk = () => {
    const orderValue = Number(formData.order_value);

    let riskScore = 0;
    const reasons = [];

    if (orderValue > 2000) {
      riskScore += 0.35;
      reasons.push("High Order Value (> ₹2,000)");
    } else if (orderValue > 1000) {
      riskScore += 0.15;
      reasons.push("Medium Order Value");
    }

    if (formData.payment_mode === "COD") {
      riskScore += 0.15;
      reasons.push("Cash on Delivery");
    }

    if (formData.is_festive_window) {
      riskScore += 0.20;
      reasons.push("Festive Window Multiplier Active");
    }

    if (formData.pincode.startsWith("11")) {
      riskScore += 0.10;
      reasons.push("Pincode Risk Baseline");
    }

    riskScore = Math.min(riskScore, 1);

    let riskLevel;
    let recommendedAction;

    if (riskScore < 0.3) {
      riskLevel = "Low";
      recommendedAction = "Ship Normal COD";
    } else if (riskScore < 0.6) {
      riskLevel = "Medium";
      recommendedAction = "Require Partial Prepaid Deposit";
    } else {
      riskLevel = "High";
      recommendedAction = "Confirmation Call / Prepaid Only";
    }

    setResult({
      risk_score: riskScore,
      risk_level: riskLevel,
      reasons,
      recommended_action: recommendedAction,
    });
  };

  return (
    <section className="simulation-section">
      <div className="simulation-header">
        <div>
          <h2>Risk Simulation</h2>
          <p>
            Simulate a COD order and evaluate its RTO risk.
          </p>
        </div>
      </div>

      <div className="simulation-grid">
        <div className="simulation-form">
          <h3>Order Details</h3>

          <label>
            Order Value
            <input
              type="number"
              name="order_value"
              placeholder="e.g. 2450"
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
              <option value="COD">COD</option>
              <option value="Prepaid">Prepaid</option>
            </select>
          </label>

          <label>
            Pincode
            <input
              type="text"
              name="pincode"
              placeholder="e.g. 110001"
              value={formData.pincode}
              onChange={handleChange}
            />
          </label>

          <label>
            Category
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
            >
              <option value="Apparel">Apparel</option>
              <option value="Electronics">Electronics</option>
              <option value="Fashion">Fashion</option>
              <option value="Home & Kitchen">
                Home & Kitchen
              </option>
            </select>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              name="is_festive_window"
              checked={formData.is_festive_window}
              onChange={handleChange}
            />

            Festive Window
          </label>

          <button
            className="simulate-button"
            onClick={calculateRisk}
          >
            Analyze Risk
          </button>
        </div>

        <div className="simulation-result">
          {!result ? (
            <div className="empty-result">
              <h3>Risk Result</h3>
              <p>
                Enter order details and click
                <strong> Analyze Risk </strong>
                to see the prediction.
              </p>
            </div>
          ) : (
            <>
              <div className="result-header">
                <div>
                  <span>Risk Score</span>

                  <strong>
                    {Math.round(result.risk_score * 100)}%
                  </strong>
                </div>

                <RiskBadge level={result.risk_level} />
              </div>

              <div className="result-section">
                <h3>Why is this risky?</h3>

                {result.reasons.length > 0 ? (
                  <ul className="reason-list">
                    {result.reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No major risk factors detected.</p>
                )}
              </div>

              <div className="result-section">
                <h3>Recommended Action</h3>

                <div className="recommendation">
                  {result.recommended_action}
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