import { useEffect, useMemo, useState } from "react";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import OrderFeed from "../components/OrderFeed";
import OrderDrawer from "../components/OrderDrawer";
import Filters from "../components/Filters";

import mockOrders from "../data/mockOrders";
import { getEvaluatedOrders } from "../services/api";

function Orders() {
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const [riskFilter, setRiskFilter] = useState("All");
  const [paymentFilter, setPaymentFilter] = useState("All");
  const [sortBy, setSortBy] = useState("risk-desc");

  // Load orders from MongoDB
  useEffect(() => {
    async function loadOrders() {
      try {
        const liveOrders = await getEvaluatedOrders(100);
        if (liveOrders && liveOrders.length > 0) {
          setOrders(liveOrders);
        } else {
          setOrders(mockOrders);
        }
      } catch (err) {
        console.warn("Backend unavailable, using mock orders:", err);
        setOrders(mockOrders);
      } finally {
        setLoading(false);
      }
    }

    loadOrders();
  }, []);

  // ========================================
  // FILTERING AND SORTING
  // ========================================

  const filteredOrders = useMemo(() => {
    let result = [...orders];

    // Risk filter
    if (riskFilter !== "All") {
      result = result.filter(
        (order) => order.risk_level === riskFilter
      );
    }

    // Payment filter
    if (paymentFilter !== "All") {
      result = result.filter(
        (order) => order.payment_mode === paymentFilter
      );
    }

    // Sorting
    result.sort((a, b) => {
      switch (sortBy) {
        case "risk-desc":
          return b.risk_score - a.risk_score;

        case "risk-asc":
          return a.risk_score - b.risk_score;

        case "value-desc":
          return b.order_value - a.order_value;

        case "value-asc":
          return a.order_value - b.order_value;

        default:
          return 0;
      }
    });

    return result;
  }, [orders, riskFilter, paymentFilter, sortBy]);

  return (
    <div className="app">
      <Sidebar />

      <div className="main-content">
        <Header />

        <main className="dashboard">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1>Evaluated Orders Feed</h1>
              <p className="subtitle">
                Monitor risk classification and recommended intervention actions for all incoming orders.
              </p>
            </div>
            {!loading && (
              <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                Total: <strong>{filteredOrders.length} orders</strong>
              </span>
            )}
          </div>

          <Filters
            riskFilter={riskFilter}
            setRiskFilter={setRiskFilter}
            paymentFilter={paymentFilter}
            setPaymentFilter={setPaymentFilter}
            sortBy={sortBy}
            setSortBy={setSortBy}
          />

          <OrderFeed
            orders={filteredOrders}
            onSelectOrder={setSelectedOrder}
          />

          <OrderDrawer
            order={selectedOrder}
            onClose={() => setSelectedOrder(null)}
          />
        </main>
      </div>
    </div>
  );
}

export default Orders;