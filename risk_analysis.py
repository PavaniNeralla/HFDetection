# ✅ Determine Risk Dynamically
def determine_risk(risk_values, threshold_settings):
    for metric, value in risk_values.items():
        threshold = threshold_settings.get(metric, {})
        condition = threshold.get("condition", "less than")
        limit1 = threshold.get("value", 40)
        limit2 = threshold.get("value2", None)

        # ✅ Ensure EF values below the threshold are correctly classified as High Risk
        if "EF" in metric and value < 40:  
            return "High Risk"
        
        if condition == "less than" and value < limit1:
            return "High Risk"
        elif condition == "greater than" and value > limit1:
            return "High Risk"
        elif condition == "between" and limit2 is not None:
            if not (limit1 <= value <= limit2):
                return "High Risk"
    return "Low Risk"
