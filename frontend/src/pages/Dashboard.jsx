import { useEffect, useState } from "react";

import Header from "../components/Header";
import Sidebar from "../components/Sidebar";
import KpiCard from "../components/KpiCard";
import OrderFeed from "../components/OrderFeed";
import OrderDrawer from "../components/OrderDrawer";

import mockOrders from "../data/mockOrders";
import { getDashboardSummary, getEvaluatedOrders } from "../services/api";

function Dashboard() {
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orders, setOrders] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch live orders and summary from MongoDB
  useEffect(() => {
    async function loadLiveData() {
      try {
        const [liveOrders, liveKpis] = await Promise.all([
          getEvaluatedOrders(10),
          getDashboardSummary(),
        ]);

        // If DB has evaluated orders, use them; otherwise fallback to mockOrders
        if (liveOrders && liveOrders.length > 0) {
          setOrders(liveOrders);
        } else {
          setOrders(mockOrders);
        }

        if (liveKpis && liveKpis.total_orders > 0) {
          setKpis(liveKpis);
        }
      } catch (err) {
        console.warn("Backend unavailable, using local mock data:", err);
        setOrders(mockOrders);
      } finally {
        setLoading(false);
      }
    }

    loadLiveData();
  }, []);

  // Compute metrics (use backend KPIs if available, else derive from current orders)
  const totalOrders = kpis?.total_orders ?? orders.length;

  const highRiskOrders =
    kpis?.high_risk_orders ??
    orders.filter((order) => order.risk_level === "High").length;

  const rtoRiskPercentage =
    kpis?.rto_risk_percentage ??
    (totalOrders > 0 ? ((highRiskOrders / totalOrders) * 100).toFixed(1) : "0.0");

  const expectedLoss =
    kpis?.expected_loss_prevented ??
    orders.reduce((total, order) => total + (order.expected_loss_prevented || 0), 0);

  const totalOrderValue =
    kpis?.total_order_value ??
    orders.reduce((total, order) => total + (order.order_value || 0), 0);

  const recentOrders = orders.slice(0, 5);

  return (
    <div className="app">
      <Sidebar />

      <div className="main-content">
        <Header />

        <main className="dashboard">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1>Risk Intelligence Dashboard</h1>
              <p className="subtitle">
                Live RTO risk scoring, financial protection metrics, and operational decision feed.
              </p>
            </div>
            {!loading && kpis && (
              <span style={{ fontSize: "0.75rem", backgroundColor: "#dcfce7", color: "#15803d", padding: "0.35rem 0.75rem", borderRadius: "9999px", fontWeight: 600 }}>
                ● Connected to MongoDB Atlas
              </span>
            )}
          </div>

          <div className="kpi-grid">
            <KpiCard
              title="Total Orders Analyzed"
              value={totalOrders}
              change={`${orders.length} in active feed`}
              trend="up"
            />

            <KpiCard
              title="Flagged High Risk"
              value={highRiskOrders}
              change={`${rtoRiskPercentage}% risk rate`}
              trend="down"
            />

            <KpiCard
              title="Potential Loss Prevented"
              value={`₹${Math.round(expectedLoss).toLocaleString()}`}
              change="From high-risk COD interventions"
              trend="up"
            />

            <KpiCard
              title="Total Monitored Value"
              value={`₹${Math.round(totalOrderValue).toLocaleString()}`}
              change="Total order volume processed"
              trend="up"
            />
          </div>

          <section className="feed-section">
            <div className="section-header">
              <h2>Recent Live Evaluated Orders</h2>
              <span>Real-time model inference feed</span>
            </div>

            <OrderFeed
              orders={recentOrders}
              onSelectOrder={setSelectedOrder}
            />
          </section>

          <OrderDrawer
            order={selectedOrder}
            onClose={() => setSelectedOrder(null)}
          />
        </main>
      </div>
    </div>
  );
}

export default Dashboard;