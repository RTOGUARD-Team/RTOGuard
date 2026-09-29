import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function Analytics({ orders }) {
  const riskData = [
    {
      name: "Low",
      orders: orders.filter((order) => order.risk_level === "Low").length,
    },
    {
      name: "Medium",
      orders: orders.filter((order) => order.risk_level === "Medium").length,
    },
    {
      name: "High",
      orders: orders.filter((order) => order.risk_level === "High").length,
    },
  ];

  const valueData = [
    {
      name: "Low",
      value: orders
        .filter((order) => order.risk_level === "Low")
        .reduce((total, order) => total + order.order_value, 0),
    },
    {
      name: "Medium",
      value: orders
        .filter((order) => order.risk_level === "Medium")
        .reduce((total, order) => total + order.order_value, 0),
    },
    {
      name: "High",
      value: orders
        .filter((order) => order.risk_level === "High")
        .reduce((total, order) => total + order.order_value, 0),
    },
  ];

  const COLORS = ["#22c55e", "#f59e0b", "#ef4444"];

  return (
    <section className="analytics-section">
      <div className="analytics-header">
        <div>
          <h2>Risk Analytics</h2>
          <p>Overview of current order risk distribution</p>
        </div>
      </div>

      <div className="analytics-grid">
        <div className="chart-card">
          <h3>Risk Distribution</h3>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={riskData}
                  dataKey="orders"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {riskData.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={COLORS[index]}
                    />
                  ))}
                </Pie>

                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <h3>Order Value by Risk</h3>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={valueData}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="name" />

                <YAxis />

                <Tooltip
                  formatter={(value) =>
                    `₹${value.toLocaleString("en-IN")}`
                  }
                />

                <Bar
                  dataKey="value"
                  fill="#334155"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Analytics;