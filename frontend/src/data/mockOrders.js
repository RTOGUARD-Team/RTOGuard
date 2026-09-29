const mockOrders = [
  {
    order_id: "ORD-45210",
    customer_id: "CUS-1001",
    order_value: 2450,
    payment_mode: "COD",
    pincode: "110001",
    category: "Apparel",
    risk_score: 0.82,
    risk_level: "High",
    reasons: [
      "High Order Value",
      "Festive Window",
      "Pincode Tier 2 Baseline",
    ],
    recommended_action: "Confirmation Call / Prepaid Only",
    expected_loss_prevented: 650,
  },

  {
    order_id: "ORD-45211",
    customer_id: "CUS-1002",
    order_value: 1299,
    payment_mode: "COD",
    pincode: "411001",
    category: "Electronics",
    risk_score: 0.51,
    risk_level: "Medium",
    reasons: [
      "Medium Order Value",
      "Pincode Risk",
    ],
    recommended_action: "Require Partial Prepaid Deposit",
    expected_loss_prevented: 280,
  },

  {
    order_id: "ORD-45212",
    customer_id: "CUS-1003",
    order_value: 799,
    payment_mode: "COD",
    pincode: "400001",
    category: "Fashion",
    risk_score: 0.18,
    risk_level: "Low",
    reasons: [
      "Low Historical RTO Risk",
    ],
    recommended_action: "Ship Normal COD",
    expected_loss_prevented: 0,
  },

  {
    order_id: "ORD-45213",
    customer_id: "CUS-1004",
    order_value: 3200,
    payment_mode: "COD",
    pincode: "560001",
    category: "Electronics",
    risk_score: 0.71,
    risk_level: "High",
    reasons: [
      "High Order Value",
      "High-Risk Pincode",
    ],
    recommended_action: "Confirmation Call / Prepaid Only",
    expected_loss_prevented: 720,
  },

  {
    order_id: "ORD-45214",
    customer_id: "CUS-1005",
    order_value: 1499,
    payment_mode: "COD",
    pincode: "380001",
    category: "Home & Kitchen",
    risk_score: 0.36,
    risk_level: "Medium",
    reasons: [
      "Medium Risk Pincode",
    ],
    recommended_action: "Require Partial Prepaid Deposit",
    expected_loss_prevented: 190,
  },
];

export default mockOrders;