function Filters({
  riskFilter,
  setRiskFilter,
  paymentFilter,
  setPaymentFilter,
  sortBy,
  setSortBy,
}) {
  return (
    <div className="filters">
      <select
        value={riskFilter}
        onChange={(event) => setRiskFilter(event.target.value)}
      >
        <option value="All">All Risk Levels</option>
        <option value="Low">Low Risk</option>
        <option value="Medium">Medium Risk</option>
        <option value="High">High Risk</option>
      </select>

      <select
        value={paymentFilter}
        onChange={(event) => setPaymentFilter(event.target.value)}
      >
        <option value="All">All Payment Modes</option>
        <option value="COD">COD</option>
        <option value="Prepaid">Prepaid</option>
      </select>

      <select
        value={sortBy}
        onChange={(event) => setSortBy(event.target.value)}
      >
        <option value="risk-desc">Highest Risk</option>
        <option value="risk-asc">Lowest Risk</option>
        <option value="value-desc">Highest Order Value</option>
        <option value="value-asc">Lowest Order Value</option>
      </select>
    </div>
  );
}

export default Filters;