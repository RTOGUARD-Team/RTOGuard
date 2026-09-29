import { useState } from "react";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import KpiCard from "../components/KpiCard";
import OrderFeed from "../components/OrderFeed";
import OrderDrawer from "../components/OrderDrawer";

import mockOrders from "../data/mockOrders";

function Dashboard() {
  const [selectedOrder, setSelectedOrder] = useState(null);

  // Dashboard KPI calculations
  const totalOrders = mockOrders.length;

  const highRiskOrders = mockOrders.filter(
    (order) => order.risk_level === "High"
  ).length;

  const rtoRiskPercentage =
    totalOrders > 0
      ? ((highRiskOrders / totalOrders) * 100).toFixed(1)
      : "0.0";

  const expectedLoss = mockOrders.reduce(
    (total, order) =>
      total + order.expected_loss_prevented,
    0
  );

  const totalOrderValue = mockOrders.reduce(
    (total, order) =>
      total + order.order_value,
    0
  );

  // Show only a few recent orders on Dashboard
  const recentOrders = mockOrders.slice(0, 5);

  return (
    <div className="app">

      <Sidebar />

      <div className="main-content">

        <Header />

        <main className="dashboard">

          {/* Dashboard Heading */}

          <h1>RTOGuard Dashboard</h1>

          <p className="subtitle">
            Monitor COD orders, RTO risk and prevention actions.
          </p>


          {/* KPI CARDS */}

          <section className="kpi-grid">

            <KpiCard
              title="Total Orders"
              value={totalOrders}
              subtitle="Orders processed"
            />

            <KpiCard
              title="High Risk"
              value={`${rtoRiskPercentage}%`}
              subtitle="Orders classified as high risk"
            />

            <KpiCard
              title="Order Value"
              value={`₹${totalOrderValue.toLocaleString("en-IN")}`}
              subtitle="Total COD order value"
            />

            <KpiCard
              title="Loss Prevented"
              value={`₹${expectedLoss.toLocaleString("en-IN")}`}
              subtitle="Expected loss prevented"
            />

          </section>


          {/* RECENT ORDERS */}

          <section className="order-section">

            <div className="section-header order-header">

              <div>

                <h2>Recent Orders</h2>

                <p>
                  Showing {recentOrders.length} recent orders
                </p>

              </div>

            </div>

            <OrderFeed
              orders={recentOrders}
              onSelect={setSelectedOrder}
            />

          </section>

        </main>

      </div>


      {/* ORDER DETAILS DRAWER */}

      <OrderDrawer
        order={selectedOrder}
        onClose={() => setSelectedOrder(null)}
      />

    </div>
  );
}

export default Dashboard;