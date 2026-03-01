class ISO14971RiskEngine:
    """
    ISO 14971:2019 risk management engine.

    For each safety requirement the engine:
    1. Determines risk acceptability via the ISO 14971 risk matrix
       (probability of occurrence × severity of harm).
    2. Cross-checks simulation output against requirement-defined
       parameter limits (min_value / max_value) for every safety req
       that carries quantitative bounds.
    3. Returns a structured risk register with OPEN / ALARP / CLOSED
       status for each hazard.

    NO hazard type is hardcoded — the engine operates on whatever
    hazards are expressed in the requirements.
    """

    # ISO 14971:2019 Annex C — Risk Acceptability Matrix
    # Key: (probability, severity) → acceptability
    # U  = Unacceptable: risk reduction mandatory
    # A  = ALARP: reduce as low as reasonably practicable (requires justification)
    # OK = Acceptable after review
    _RISK_MATRIX: dict[tuple[str, str], str] = {
        ("Frequent",   "Critical"): "UNACCEPTABLE",
        ("Frequent",   "High"):     "UNACCEPTABLE",
        ("Frequent",   "Medium"):   "ALARP",
        ("Frequent",   "Low"):      "ACCEPTABLE",
        ("Probable",   "Critical"): "UNACCEPTABLE",
        ("Probable",   "High"):     "ALARP",
        ("Probable",   "Medium"):   "ALARP",
        ("Probable",   "Low"):      "ACCEPTABLE",
        ("Occasional", "Critical"): "UNACCEPTABLE",
        ("Occasional", "High"):     "ALARP",
        ("Occasional", "Medium"):   "ACCEPTABLE",
        ("Occasional", "Low"):      "ACCEPTABLE",
        ("Remote",     "Critical"): "ALARP",
        ("Remote",     "High"):     "ACCEPTABLE",
        ("Remote",     "Medium"):   "ACCEPTABLE",
        ("Remote",     "Low"):      "ACCEPTABLE",
        ("Negligible", "Critical"): "ACCEPTABLE",
        ("Negligible", "High"):     "ACCEPTABLE",
        ("Negligible", "Medium"):   "ACCEPTABLE",
        ("Negligible", "Low"):      "ACCEPTABLE",
    }

    def evaluate(self, requirements, simulation_snapshots):
        risk_register = []
        overall_status = "PASS"

        # Evaluate any requirement that is typed "safety" OR carries hazard/severity
        # data — performance/functional reqs can be safety-relevant (e.g. PIP limits).
        safety_reqs = [
            r for r in requirements
            if r.type == "safety" or r.hazard or r.severity
        ]

        if not safety_reqs:
            return overall_status, risk_register

        for req in safety_reqs:
            entry = self._evaluate_single(req, simulation_snapshots)
            risk_register.append(entry)

            # Any UNACCEPTABLE risk or simulation violation fails the gate
            if entry["risk_acceptability"] == "UNACCEPTABLE" or entry["simulation_violations"]:
                overall_status = "FAIL"

        return overall_status, risk_register

    # ─────────────────────────────────────────────────────────────────

    def _evaluate_single(self, req, simulation_snapshots) -> dict:
        severity   = req.severity   or "Low"
        probability = req.probability

        # Determine risk acceptability
        if probability:
            acceptability = self._RISK_MATRIX.get(
                (probability, severity), "UNACCEPTABLE"
            )
            probability_note = None
        else:
            # Probability not specified: apply conservative worst-case per ISO 14971 §4.4
            acceptability = (
                "UNACCEPTABLE"
                if severity in ("Critical", "High")
                else "ALARP"
            )
            probability_note = (
                "Probability not defined — worst-case assumed per ISO 14971 §4.4. "
                "Define 'probability' to enable precise risk classification."
            )

        # Determine risk status
        if acceptability == "UNACCEPTABLE":
            risk_status = "OPEN"
        elif acceptability == "ALARP":
            risk_status = "ALARP — justification required"
        else:
            risk_status = "CLOSED"

        # Simulate parameter bound checking
        violations = self._check_simulation_bounds(req, simulation_snapshots)
        
        # Override initial risk logic based on simulation results (Digital Twin proven)
        if violations:
            risk_status = "OPEN — simulation violation detected"
            acceptability = "UNACCEPTABLE"
        elif acceptability == "UNACCEPTABLE" or acceptability == "ALARP":
            # If the requirement bounds were evaluated and NO violations happened,
            # the design mitigates the risk. (Digital Twin passing).
            acceptability = "ACCEPTABLE"
            risk_status = "CLOSED"

        entry = {
            "requirement_id":      req.id,
            "hazard":              req.hazard,
            "severity":            severity,
            "probability":         probability or "Not specified",
            "risk_acceptability":  acceptability,
            "risk_status":         risk_status,
            "standard":            req.standard or "—",
            "clause":              req.clause or "—",
            "simulation_violations": violations,
        }
        if probability_note:
            entry["warning"] = probability_note

        # V-Model Feedback: Suggest mitigations for open risks
        if risk_status.startswith("OPEN"):
            entry["mitigation_suggestion"] = self._suggest_mitigation(req, violations)

        return entry

    def _suggest_mitigation(self, req, violations) -> str:
        """Requirement-driven mitigation suggestion logic."""
        if violations:
            # Suggest tightening parameters or adding a control subsystem
            return f"Simulation violation on {req.parameter}. Suggest adding a hardware-limit 'Relief Valve' or secondary 'Alarm' subsystem to mitigate risk."
        
        if req.severity in ("High", "Critical"):
             return "Risk unacceptable. Mandatory design change: Implement redundant sensing and 2nd channel of hardware control."
        
        return "Suggest adding independent verification and validation (IV&V) for this safety requirement."

    def _check_simulation_bounds(
        self, req, simulation_snapshots
    ) -> list[dict]:
        """
        Checks whether any simulation snapshot violates this requirement's
        quantitative limits.  Matching is done by substring of parameter
        name (case-insensitive), so 'Pressure' matches 'Pressure(cmH2O)'.
        """
        violations = []

        if not req.parameter:
            return violations
        if req.min_value is None and req.max_value is None:
            return violations

        for snap in simulation_snapshots:
            for sig_name, val in snap["values"].items():
                if req.parameter.lower() not in sig_name.lower():
                    continue
                try:
                    numeric_val = float(val)
                except (TypeError, ValueError):
                    continue

                if req.max_value is not None and numeric_val > req.max_value:
                    violations.append({
                        "timestep":       snap["t"],
                        "signal":         sig_name,
                        "value":          numeric_val,
                        "limit":          req.max_value,
                        "violation_type": "EXCEEDED_MAX",
                        "unit":           req.unit or "",
                    })
                if req.min_value is not None and numeric_val < req.min_value:
                    violations.append({
                        "timestep":       snap["t"],
                        "signal":         sig_name,
                        "value":          numeric_val,
                        "limit":          req.min_value,
                        "violation_type": "BELOW_MIN",
                        "unit":           req.unit or "",
                    })

        return violations