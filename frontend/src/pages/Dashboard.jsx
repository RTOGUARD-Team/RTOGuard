function Dashboard() {
  const [selectedOrder, setSelectedOrder] = useState(null);

  const [riskFilter, setRiskFilter] = useState("All");
  const [paymentFilter, setPaymentFilter] = useState("All");
  const [sortBy, setSortBy] = useState("risk-desc");

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


  // ================================
  // DASHBOARD CALCULATIONS
  // ================================

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


  return (
    <div className="app">
      <Sidebar />

      <div className="main-content">
        <Header />

        <main className="dashboard">
          <h1>RTOGuard Dashboard</h1>

          <p className="subtitle">
            Monitor COD orders, RTO risk and prevention actions.
          </p>

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

          <Analytics orders={mockOrders} />

          <section className="order-section">
            <div className="section-header order-header">
              <div>
                <h2>Recent Orders</h2>

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

export default Dashboard;