import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import SimulationCard from "../components/SimulationCard";

function Simulation() {
  return (
    <div className="app">

      <Sidebar />

      <div className="main-content">

        <Header />

        <main className="dashboard">

          <h1>Risk Simulation</h1>

          <p className="subtitle">
            Analyze the RTO risk of a COD order before processing it.
          </p>

          <SimulationCard />

        </main>

      </div>

    </div>
  );
}

export default Simulation;