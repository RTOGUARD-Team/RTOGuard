import OrderRow from "./OrderRow";

function OrderFeed({ orders, onSelect }) {
  return (
    <div className="table-container">
      {orders.length === 0 ? (
        <div className="no-orders">
          No orders match the selected filters.
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Order Value</th>
              <th>Risk Score</th>
              <th>Risk Level</th>
              <th>Recommended Action</th>
            </tr>
          </thead>

          <tbody>
            {orders.map((order) => (
              <OrderRow
                key={order.order_id}
                order={order}
                onSelect={onSelect}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default OrderFeed;