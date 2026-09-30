/**
 * RTOGuard Frontend API Service
 * Central communication layer connecting React components to the FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Score an incoming order using RTO ML models + Action Engine + Cost Calculator
 * @param {Object} orderData Raw order details (order_id, customer_id, order_value, pincode, payment_mode, etc.)
 * @returns {Promise<Object>} Evaluated decision including risk_score, risk_level, recommended_action, net_impact
 */
export async function scoreOrder(orderData) {
  const response = await fetch(`${API_BASE_URL}/rto/score-order`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(orderData),
  });

  if (!response.ok) {
    const errorDetails = await response.json().catch(() => ({ detail: "Network response was not ok" }));
    throw new Error(errorDetails.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

/**
 * Health check to verify FastAPI and MongoDB connectivity
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}
