# analyze_pcb.py

import numpy as np
from PIL import Image, ImageFilter
import io
import os
import json

class PCBAnalyzer:
    """Class for analyzing PCB images with type-specific logic."""

    def __init__(self):
        """Initialize the PCB analyzer."""
        self.quality_classes = ['basic', 'enhanced', 'comprehensive']
        self.cert_classes = ['CE', 'RoHS', 'UL', 'FCC', 'ISO9001', 'IEC60950', 'IATF16949']

    def analyze_image(self, image_bytes, analysis_option=1):
        """
        Analyze a PCB image using a rule-based system that is specific
        to the detected PCB type and characteristics.

        Args:
            image_bytes: Raw image bytes from the uploaded file.
            analysis_option: The user's choice of analysis (1, 2, or 3).

        Returns:
            dict: A dictionary containing the detailed analysis results.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            features = self._detect_pcb_features(image)

            results = {}

            # --- New Type-Specific Logic ---
            # Determine quality and certification based on detected features
            quality_result, cert_list = self._get_requirements_by_type(features)

            # 1. Quality Check Analysis
            if analysis_option in [1, 2]:
                results["quality_check_required"] = f"{quality_result.capitalize()} (Recommended for {features['pcb_type']} type)"
                results["quality_details"] = self._get_quality_check_details(quality_result, features)

            # 2. Certification Analysis
            if analysis_option in [1, 3]:
                if cert_list:
                    cert_string = "; ".join(cert_list)
                    results["certification_needed"] = f"{cert_string} (Recommended for {features['intended_application']} application)"
                else:
                    results["certification_needed"] = "No specific certifications typically required."
                results["certification_details"] = self._get_certification_details(cert_list, features)
            
            # Format the final output string
            results["details"] = self._format_details(results, features, analysis_option)
            
            return results

        except Exception as e:
            return {
                "quality_check_required": "Error",
                "certification_needed": "Error",
                "details": f"An error occurred during image processing: {e}"
            }

    def _get_requirements_by_type(self, features):
        """
        This is the core rule engine. It determines requirements based on PCB features.
        """
        pcb_type = features['pcb_type']
        density = features['component_density']

        quality_level = 'basic'
        certifications = {'CE', 'RoHS'} # Start with the most common ones

        # --- Quality Level Rules ---
        if pcb_type in ['multilayer', 'high_frequency', 'high_power', 'rigid_flex']:
            quality_level = 'comprehensive'
        elif pcb_type in ['double_sided', 'flexible']:
            quality_level = 'enhanced'
        elif density in ['high', 'very_high']:
            quality_level = 'comprehensive'
        elif density == 'medium':
            quality_level = 'enhanced'

        # --- Certification Rules ---
        if features['intended_application'] in ['industrial', 'medical', 'automotive', 'aerospace', 'military']:
            certifications.add('UL') # Safety is key
            certifications.add('ISO9001') # Quality management

        if features['intended_application'] in ['telecom', 'computing', 'iot']:
            certifications.add('FCC') # For devices that emit radio frequencies

        if features['intended_application'] == 'automotive':
            certifications.add('IATF16949')

        if features['intended_application'] == 'medical':
            certifications.add('IEC60950') # Or ISO 13485 for medical devices

        return quality_level, sorted(list(certifications))

    def _detect_pcb_features(self, image):
        """
        Enhanced feature detection to better guess PCB type and application.
        This is still a simulation but provides more realistic inputs for the rules engine.
        """
        img_gray = image.convert('L').resize((224, 224))
        img_color = image.convert('RGB').resize((224, 224))
        
        # Color Analysis
        mean_color = np.mean(np.array(img_color), axis=(0, 1))
        
        # Texture/Complexity Analysis using edge detection
        edges = img_gray.filter(ImageFilter.FIND_EDGES)
        edge_intensity = np.mean(np.array(edges))

        # --- Rule-based Feature Estimation ---
        pcb_type = 'single_sided'
        intended_application = 'consumer_electronics'

        if 15 < edge_intensity <= 30:
            pcb_type = 'double_sided'
            intended_application = 'industrial'
        elif edge_intensity > 30:
            pcb_type = 'multilayer'
            intended_application = 'computing'

        # Color-based overrides
        # Blue PCBs are often used for high-frequency applications
        if mean_color[2] > mean_color[0] and mean_color[2] > mean_color[1]:
            pcb_type = 'high_frequency'
            intended_application = 'telecom'
        # Yellow/Amber PCBs are often flexible
        elif mean_color[0] > 140 and mean_color[1] > 120 and mean_color[2] < 100:
            pcb_type = 'flexible'
            intended_application = 'wearables'

        # Density classification
        if edge_intensity < 15:
            component_density = "low"
        elif edge_intensity < 25:
            component_density = "medium"
        elif edge_intensity < 35:
            component_density = "high"
        else:
            component_density = "very_high"

        return {
            "pcb_type": pcb_type,
            "component_density": component_density,
            "intended_application": intended_application,
            "estimated_layer_count": max(1, int(edge_intensity / 10)),
            "issues": ["none detected"] # Placeholder
        }

    def _get_quality_check_details(self, quality_level, features):
        """Generates a list of recommended quality checks."""
        # This function can remain largely the same, as it's already detailed.
        # It will now receive more accurate inputs.
        pcb_type = features["pcb_type"]
        
        base_checks = ["Visual inspection for obvious defects", "Solder joint inspection"]
        checks = []

        if quality_level == "basic":
            checks = base_checks + ["Basic continuity testing"]
        elif quality_level == "enhanced":
            checks = base_checks + ["Automated Optical Inspection (AOI)", "Full continuity/isolation testing"]
        elif quality_level == "comprehensive":
            checks = base_checks + ["AOI", "Automated X-ray Inspection (AXI)", "In-Circuit Testing (ICT)"]

        # Add type-specific checks
        if pcb_type == "multilayer":
            checks.append("Layer registration verification")
        if pcb_type in ["flexible", "rigid_flex"]:
            checks.append("Flexibility and bend testing for delamination")
        if pcb_type == "high_frequency":
            checks.append("Controlled impedance testing")
        if pcb_type == "high_power":
            checks.append("Thermal stress testing & copper thickness verification")
            
        return checks

    def _get_certification_details(self, certifications, features):
        """Generates detailed descriptions for required certifications."""
        # This function can also remain the same.
        cert_details = {}
        for cert in certifications:
            if cert == "CE":
                cert_details["CE"] = "European Conformity. Mandatory for products sold in the EEA."
            elif cert == "RoHS":
                cert_details["RoHS"] = "Restriction of Hazardous Substances. Limits specific materials."
            elif cert == "UL":
                cert_details["UL"] = "Underwriters Laboratories. A key safety certification for the US market."
            elif cert == "FCC":
                cert_details["FCC"] = "Federal Communications Commission. Required for devices that emit electronic noise."
            elif cert == "ISO9001":
                cert_details["ISO9001"] = "Standard for a quality management system."
            elif cert == "IATF16949":
                cert_details["IATF16949"] = "Global quality management standard for the Automotive sector."
            elif cert == "IEC60950":
                 cert_details["IEC60950"] = "Safety standard for Information Technology Equipment, crucial for medical devices."
        return cert_details

    def _format_details(self, results, features, analysis_option):
        """Formats the final detailed output for the user."""
        details = [
            f"**Detected PCB Profile:**",
            f"- **Type:** {features['pcb_type'].replace('_', ' ').title()}",
            f"- **Probable Application:** {features['intended_application'].replace('_', ' ').title()}",
            f"- **Component Density:** {features['component_density'].title()}",
            f"- **Est. Layer Count:** {features['estimated_layer_count']}",
            "\n"
        ]
        
        if analysis_option in [1, 2] and "quality_details" in results:
            details.append("**RECOMMENDED QUALITY CHECKS:**")
            for check in results["quality_details"]:
                details.append(f"- {check}")
            details.append("\n")
            
        if analysis_option in [1, 3] and "certification_details" in results:
            details.append("**APPLICABLE CERTIFICATIONS:**")
            for cert, desc in results["certification_details"].items():
                details.append(f"- **{cert}:** {desc}")
            details.append("\n")
            
        return "\n".join(details)


# This is the main function that your app.py will call.
def analyze_pcb_image(image_bytes, analysis_option):
    """
    Entry point for PCB analysis.
    """
    analyzer = PCBAnalyzer()
    return analyzer.analyze_image(image_bytes, analysis_option)
