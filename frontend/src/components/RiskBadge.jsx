function RiskBadge({ level }) {
  return (
    <span className={`risk-badge ${level.toLowerCase()}`}>
      {level}
    </span>
  );
}

export default RiskBadge;