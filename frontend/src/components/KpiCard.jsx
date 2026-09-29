function KpiCard({ title, value, subtitle }) {
  return (
    <div className="kpi-card">
      <p className="kpi-title">{title}</p>

      <h2 className="kpi-value">{value}</h2>

      <p className="kpi-subtitle">{subtitle}</p>
    </div>
  );
}

export default KpiCard;