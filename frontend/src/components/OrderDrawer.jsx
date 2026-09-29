function OrderDrawer({ order, onClose }) {
  if (!order) {
    return null;
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="order-drawer"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-header">
          <div>
            <p className="drawer-label">Order Details</p>
            <h2>{order.order_id}</h2>
          </div>

          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="drawer-content">
          <div className="order-info-grid">
            <div>
              <span>Order Value</span>
              <strong>
                ₹{order.order_value.toLocaleString("en-IN")}
              </strong>
            </div>

            <div>
              <span>Payment Mode</span>
              <strong>{order.payment_mode}</strong>
            </div>

            <div>
              <span>Pincode</span>
              <strong>{order.pincode}</strong>
            </div>

            <div>
              <span>Category</span>
              <strong>{order.category}</strong>
            </div>
          </div>

          <div className="risk-summary">
            <div>
              <span>RTO Risk</span>
              <strong className="risk-score">
                {Math.round(order.risk_score * 100)}%
              </strong>
            </div>

            <div>
              <span>Risk Level</span>
              <span
                className={`risk-badge ${order.risk_level.toLowerCase()}`}
              >
                {order.risk_level}
              </span>
            </div>
          </div>

          <section className="drawer-section">
            <h3>Why is this risky?</h3>

            <ul className="reason-list">
              {order.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </section>

          <section className="drawer-section">
            <h3>Recommended Action</h3>

            <div className="recommendation">
              {order.recommended_action}
            </div>
          </section>

          <section className="loss-card">
            <span>Expected Loss Prevented</span>

            <strong>
              ₹
              {order.expected_loss_prevented.toLocaleString("en-IN")}
            </strong>
          </section>

          <button className="override-button">
            Override Decision
          </button>
        </div>
      </aside>
    </div>
  );
}

export default OrderDrawer;