import { useMemo, useState } from "react";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import OrderFeed from "../components/OrderFeed";
import OrderDrawer from "../components/OrderDrawer";
import Filters from "../components/Filters";

import mockOrders from "../data/mockOrders";

function Orders() {
  const [selectedOrder, setSelectedOrder] = useState(null);

  const [riskFilter, setRiskFilter] = useState("All");
  const [paymentFilter, setPaymentFilter] = useState("All");
  const [sortBy, setSortBy] = useState("risk-desc");

  // ========================================
  // FILTERING AND SORTING
  // ========================================

  const filteredOrders = useMemo(() => {
    let result = [...mockOrders];

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
  }, [riskFilter, paymentFilter, sortBy]);

  // ========================================
  // ORDERS PAGE UI
  // ========================================

  return (
    <div className="app">

      <Sidebar />

      <div className="main-content">

        <Header />

        <main className="dashboard">

          <h1>Orders</h1>

          <p className="subtitle">
            Monitor and manage COD orders based on their RTO risk.
          </p>

          <section className="order-section">

            <div className="section-header order-header">

              <div>
                <h2>All Orders</h2>

                <p>
                  Showing {filteredOrders.length} of{" "}
                  {mockOrders.length} orders
                </p>
              </div>

              <Filters
                riskFilter={riskFilter}
                setRiskFilter={setRiskFilter}
                paymentFilter={paymentFilter}
                setPaymentFilter={setPaymentFilter}
                sortBy={sortBy}
                setSortBy={setSortBy}
              />

            </div>

            <OrderFeed
              orders={filteredOrders}
              onSelect={setSelectedOrder}
            />

          </section>

        </main>

      </div>

      <OrderDrawer
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />

    </div>
  );
}

export default Orders;