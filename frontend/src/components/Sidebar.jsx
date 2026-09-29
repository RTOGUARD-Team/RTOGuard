function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        <h2>RTOGuard</h2>
        <span>AI Risk Control</span>
      </div>

      <nav>
        <a href="#" className="active">
          Dashboard
        </a>

        <a href="#">
          Orders
        </a>

        <a href="#">
          Analytics
        </a>

        <a href="#">
          Simulation
        </a>
      </nav>
    </aside>
  );
}

export default Sidebar;