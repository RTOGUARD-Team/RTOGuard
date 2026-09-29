import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">

      <div className="logo">
        <h2>RTOGuard</h2>
        <span>AI Risk Control</span>
      </div>

      <nav>

        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            isActive ? "active" : ""
          }
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/orders"
          className={({ isActive }) =>
            isActive ? "active" : ""
          }
        >
          Orders
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            isActive ? "active" : ""
          }
        >
          Analytics
        </NavLink>

        <NavLink
          to="/simulation"
          className={({ isActive }) =>
            isActive ? "active" : ""
          }
        >
          Simulation
        </NavLink>

      </nav>

    </aside>
  );
}

export default Sidebar;