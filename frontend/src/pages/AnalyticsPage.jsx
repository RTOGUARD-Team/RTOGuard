import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import Analytics from "../components/Analytics";

import mockOrders from "../data/mockOrders";

function AnalyticsPage() {
  return (
    <div className="app">

      <Sidebar />

      <div className="main-content">

        <Header />

        <main className="dashboard">

          <h1>Analytics</h1>

          <p className="subtitle">
            Analyze order risk, order value and RTO prevention performance.
          </p>

          <Analytics orders={mockOrders} />

        </main>

      </div>

    </div>
  );
}

export default AnalyticsPage;