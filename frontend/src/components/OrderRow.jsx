import RiskBadge from "./RiskBadge";
import ActionBadge from "./ActionBadge";

function OrderRow({ order, onSelect }) {
  return (
    <tr onClick={() => onSelect(order)}>
      <td>{order.order_id}</td>

      <td>₹{order.order_value.toLocaleString("en-IN")}</td>

      <td>{Math.round(order.risk_score * 100)}%</td>

      <td>
        <RiskBadge level={order.risk_level} />
      </td>

      <td>
        <ActionBadge action={order.recommended_action} />
      </td>
    </tr>
  );
}

export default OrderRow;