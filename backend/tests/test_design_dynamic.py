import sys
import os

# Ensure project root is on path when running as a script or via pytest
sys.path.append(os.getcwd())

from backend.app.core.devices.class2.ventilator import Ventilator
from backend.app.core.design_graph.builder import DesignGraphBuilder
from backend.app.core.requirements.schema import Requirement, Verification


def test_performance_req_adds_sensor():
    """Performance requirement with parameter 'Pressure' should add a 'Pressure Sensor' component."""
    req = Requirement(
        id="REQ-TEST-001",
        title="Maintain airway pressure",
        description="The system shall maintain airway pressure within safe bounds.",
        type="performance",
        priority="SHALL",
        status="Draft",
        subsystem="PneumaticsControl",
        parameter="Pressure",
        min_value=5.0,
        max_value=30.0,
        unit="cmH2O",
        verification=Verification(method="simulation", description="Simulate pressure behavior")
    )

    device = Ventilator()
    builder = DesignGraphBuilder(device)
    graph = builder.build([req])

    node = graph.subsystems.get("PneumaticsControl")
    assert node is not None, "PneumaticsControl subsystem missing from generated graph"

    # component entries are dicts with 'name'
    comp_names = [c.get("name") for c in node.components]
    assert any(n == "Pressure Sensor" for n in comp_names), f"Pressure Sensor not found in components: {comp_names}"


if __name__ == "__main__":
    test_performance_req_adds_sensor()
    print("test_design_dynamic: OK")
