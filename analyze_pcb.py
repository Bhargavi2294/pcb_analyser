# analyze_pcb.py

import numpy as np
from PIL import Image
import io
import os
import json

class PCBAnalyzer:
    """Class for analyzing PCB images."""
    
    def __init__(self):
        """Initialize the PCB analyzer."""
        self.quality_classes = ['basic', 'enhanced', 'comprehensive']
        self.cert_classes = ['CE', 'RoHS', 'UL', 'FCC', 'ISO9001', 'IEC60950', 'IATF16949', 'ISO13485', 'DO-254', 'MIL-STD-883']
        
        # Try to load class names from files
        try:
            if os.path.exists('models/quality_check_classes.json'):
                with open('models/quality_check_classes.json', 'r') as f:
                    self.quality_classes = json.load(f)
            if os.path.exists('models/certification_classes.json'):
                with open('models/certification_classes.json', 'r') as f:
                    self.cert_classes = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load class names: {e}")
    
    def analyze_image(self, image_bytes, analysis_option=1):
        """
        Analyze a PCB image.
        
        Args:
            image_bytes: Raw image bytes
            analysis_option: 1=both, 2=quality, 3=certification
            
        Returns:
            dict: Analysis results
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract basic PCB features
            features = self.detect_pcb_features(image)
            
            results = {}
            
            # Quality check prediction (option 1 or 2)
            if analysis_option in [1, 2]:
                # Determine quality level based on PCB type and features
                quality_result = self.determine_quality_check_level(features)
                    
                results["quality_check_required"] = f"{quality_result}"
                
                # Add quality check details
                quality_details = self.get_quality_check_details(quality_result, features)
                results["quality_details"] = quality_details
            
            # Certification prediction (option 1 or 3)
            if analysis_option in [1, 3]:
                # Determine certifications based on PCB type and features
                predicted_certs = self.determine_certifications(features)
                    
                cert_result = "; ".join(predicted_certs)
                results["certification_needed"] = cert_result
                
                # Add certification details
                cert_details = self.get_certification_details(predicted_certs, features)
                results["certification_details"] = cert_details
            
            # Format details
            results["details"] = self.format_details(results, features, analysis_option)
            
            return results
                
        except Exception as e:
            return {
                "quality_check_required": "Error",
                "certification_needed": "Error",
                "details": f"An error occurred during image processing: {e}"
            }
    
    def determine_quality_check_level(self, features):
        """
        Determine the quality check level based on PCB type and features.
        
        Args:
            features: Detected PCB features
            
        Returns:
            str: Quality check level (basic, enhanced, comprehensive)
        """
        pcb_type = features["pcb_type"]
        component_density = features["component_density"]
        layer_count = features["estimated_layer_count"]
        issues = features["issues"]
        
        # Default to basic quality check
        quality_level = "basic"
        
        # Upgrade based on PCB type
        if pcb_type in ["high_frequency", "high_power"]:
            quality_level = "enhanced"  # Specialized PCBs need enhanced checks
        
        # Upgrade based on component density
        if component_density in ["high", "very_high"]:
            quality_level = "enhanced"  # Dense boards need enhanced checks
        
        # Upgrade based on layer count
        if layer_count >= 4:
            quality_level = "enhanced"  # Multi-layer boards need enhanced checks
        if layer_count >= 6:
            quality_level = "comprehensive"  # Complex multi-layer boards need comprehensive checks
        
        # Upgrade based on issues
        if any(issue != "none detected" for issue in issues):
            quality_level = "enhanced"  # Boards with potential issues need enhanced checks
        
        # Special case upgrades to comprehensive
        if pcb_type == "multilayer" and component_density in ["high", "very_high"]:
            quality_level = "comprehensive"  # Complex multilayer boards need comprehensive checks
            
        if pcb_type in ["rigid_flex", "flexible"] and layer_count >= 2:
            quality_level = "comprehensive"  # Flexible PCBs with multiple layers need comprehensive checks
            
        # Application-specific upgrades
        if "medical" in features.get("application", ""):
            quality_level = "comprehensive"  # Medical applications always need comprehensive checks
            
        if "aerospace" in features.get("application", "") or "military" in features.get("application", ""):
            quality_level = "comprehensive"  # Aerospace and military applications always need comprehensive checks
            
        return quality_level
    
    def determine_certifications(self, features):
        """
        Determine required certifications based on PCB type and features.
        
        Args:
            features: Detected PCB features
            
        Returns:
            list: Required certifications
        """
        pcb_type = features["pcb_type"]
        component_density = features["component_density"]
        layer_count = features["estimated_layer_count"]
        
        # Base certifications for all PCBs
        certifications = ["CE", "RoHS"]  # Most electronic products need these
        
        # Add certifications based on PCB type
        if pcb_type == "high_frequency":
            certifications.append("FCC")  # High-frequency PCBs need FCC certification
            
        if pcb_type == "high_power":
            certifications.append("UL")  # High-power PCBs need UL certification
            
        # Add certifications based on complexity
        if component_density in ["high", "very_high"] or layer_count >= 4:
            if "UL" not in certifications:
                certifications.append("UL")  # Complex boards typically need UL
            
            # Add ISO 9001 for complex boards
            if "ISO9001" not in certifications:
                certifications.append("ISO9001")
        
        # Special PCB type certifications
        if pcb_type in ["flexible", "rigid_flex"]:
            if "IEC60950" not in certifications:
                certifications.append("IEC60950")  # Flexible PCBs often need this for safety
        
        # Application-specific certifications
        application = features.get("application", "").lower()
        
        if "medical" in application:
            if "ISO13485" not in certifications:
                certifications.append("ISO13485")  # Medical devices need ISO 13485
                
        if "automotive" in application:
            if "IATF16949" not in certifications:
                certifications.append("IATF16949")  # Automotive applications need IATF 16949
                
        if "aerospace" in application:
            if "DO-254" not in certifications:
                certifications.append("DO-254")  # Aerospace applications need DO-254
                
        if "military" in application:
            if "MIL-STD-883" not in certifications:
                certifications.append("MIL-STD-883")  # Military applications need MIL-STD-883
        
        return certifications
    
    def detect_pcb_features(self, image):
        """
        Detect features from a PCB image.
        This is a simplified implementation that uses basic image analysis.
        
        Args:
            image: PIL Image object
            
        Returns:
            dict: Detected PCB features
        """
        # Resize for analysis
        img = image.resize((224, 224))
        img_array = np.array(img)
        
        # Simple color analysis
        mean_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array, axis=(0, 1))
        
        # Simple edge detection to estimate component density
        gray = np.mean(img_array, axis=2).astype(np.uint8) if img_array.ndim > 2 else img_array
        
        # Simplified edge detection using std dev in local regions
        kernel_size = 5
        edge_map = np.zeros_like(gray)
        for i in range(kernel_size, gray.shape[0] - kernel_size):
            for j in range(kernel_size, gray.shape[1] - kernel_size):
                window = gray[i-kernel_size:i+kernel_size, j-kernel_size:j+kernel_size]
                edge_map[i, j] = np.std(window)
        
        edge_density = np.mean(edge_map)
        
        # Estimate PCB type based on color
        pcb_type = "unknown"
        if len(mean_color) == 3:  # RGB image
            if mean_color[1] > mean_color[0] and mean_color[1] > mean_color[2]:
                # Greenish - typical FR-4
                pcb_type = "standard"
                if edge_density > 20:
                    pcb_type = "multilayer"
                else:
                    pcb_type = "single_sided" if edge_density < 10 else "double_sided"
            elif mean_color[2] > mean_color[0] and mean_color[2] > mean_color[1]:
                # Bluish - often high-frequency
                pcb_type = "high_frequency"
            elif mean_color[0] > mean_color[1] and mean_color[0] > mean_color[2]:
                # Reddish - sometimes high-power or specialty
                pcb_type = "high_power"
            elif np.std(mean_color) < 10:
                # Low color variation - could be flexible
                pcb_type = "flexible"
        else:
            # Grayscale image - assume standard PCB
            pcb_type = "single_sided" if edge_density < 10 else "double_sided"
            
        # Estimate component density
        if edge_density < 10:
            component_density = "low"
        elif edge_density < 15:
            component_density = "medium"
        elif edge_density < 20:
            component_density = "high"
        else:
            component_density = "very_high"
            
        # Estimate layer count based on edge complexity
        layer_count = max(1, min(8, int(edge_density / 5)))
        
        # Check for potential issues
        issues = []
        if np.max(std_color) > 60 if len(std_color) == 3 else std_color > 60:
            issues.append("potential color inconsistency")
        if edge_density > 25:
            issues.append("high complexity - careful inspection recommended")
            
        # Attempt to guess application from visual features
        application = self.guess_application(pcb_type, component_density, layer_count, edge_density)
            
        return {
            "pcb_type": pcb_type,
            "component_density": component_density,
            "estimated_layer_count": layer_count,
            "edge_density": edge_density,
            "issues": issues if issues else ["none detected"],
            "application": application
        }
    
    def guess_application(self, pcb_type, component_density, layer_count, edge_density):
        """
        Make an educated guess about the PCB application based on visual features.
        This is simplified and would be much more accurate with actual ML.
        
        Args:
            pcb_type: Detected PCB type
            component_density: Detected component density
            layer_count: Estimated layer count
            edge_density: Detected edge density
            
        Returns:
            str: Guessed application
        """
        # Simple rule-based application guessing
        if pcb_type == "high_frequency" and component_density in ["high", "very_high"]:
            return "telecommunications"
            
        if pcb_type == "high_power" and layer_count >= 4:
            return "industrial_control"
            
        if pcb_type == "flexible":
            if component_density in ["high", "very_high"]:
                return "medical_wearable"
            else:
                return "consumer_electronics"
                
        if pcb_type == "rigid_flex" and layer_count >= 6:
            return "aerospace"
            
        if pcb_type == "multilayer" and layer_count >= 6 and component_density == "very_high":
            return "computing"
            
        # Default applications based on complexity
        if component_density == "very_high" and layer_count >= 6:
            return "medical_critical"
            
        if component_density == "high" and layer_count >= 4:
            return "automotive"
            
        if component_density == "medium" and layer_count >= 2:
            return "industrial_control"
            
        # Default for simpler boards
        return "consumer_electronics"
    
    def get_quality_check_details(self, quality_level, features):
        """
        Get detailed quality check requirements based on quality level and PCB features.
        
        Args:
            quality_level: Predicted quality check level
            features: Detected PCB features
            
        Returns:
            list: Detailed quality check requirements
        """
        pcb_type = features["pcb_type"]
        component_density = features["component_density"]
        issues = features["issues"]
        application = features.get("application", "")
        
        # Base checks for all PCBs
        base_checks = [
            "Visual inspection for obvious defects",
            "Dimensional verification",
            "Solder joint inspection"
        ]
        
        # Additional checks based on quality level
        additional_checks = []
        
        if quality_level == "basic":
            additional_checks = [
                "Basic continuity testing",
                "Simple functional testing"
            ]
        elif quality_level == "enhanced":
            additional_checks = [
                "Automated Optical Inspection (AOI)",
                "Complete continuity and isolation testing",
                "Functional testing with basic parameters"
            ]
        elif quality_level == "comprehensive":
            additional_checks = [
                "Automated Optical Inspection (AOI)",
                "Automated X-ray Inspection (AXI)",
                "In-Circuit Testing (ICT)",
                "Flying Probe Testing",
                "Functional testing with extended parameters",
                "Thermal stress testing"
            ]
            
        # PCB type specific checks
        type_specific_checks = []
        
        if pcb_type == "multilayer":
            type_specific_checks.append("Layer-to-layer registration verification")
            type_specific_checks.append("Buried/blind via inspection")
        elif pcb_type == "flexible" or pcb_type == "rigid_flex":
            type_specific_checks.append("Flexibility and bend testing")
            type_specific_checks.append("Delamination inspection")
        elif pcb_type == "high_frequency":
            type_specific_checks.append("Impedance testing")
            type_specific_checks.append("Signal integrity verification")
        elif pcb_type == "high_power":
            type_specific_checks.append("Copper thickness verification")
            type_specific_checks.append("Thermal performance testing")
            
        # Application-specific checks
        app_specific_checks = []
        
        if "medical" in application:
            app_specific_checks.append("Biocompatibility verification (if applicable)")
            app_specific_checks.append("Extended reliability testing")
            
        if "automotive" in application:
            app_specific_checks.append("Vibration and shock testing")
            app_specific_checks.append("Temperature cycling tests")
            
        if "aerospace" in application or "military" in application:
            app_specific_checks.append("Extended environmental stress screening")
            app_specific_checks.append("Conformal coating inspection")
            app_specific_checks.append("100% functional testing")
            
        # Add issue-specific checks
        issue_specific_checks = []
        for issue in issues:
            if issue != "none detected":
                issue_specific_checks.append(f"Detailed inspection for {issue}")
                
        # Combine all checks
        all_checks = base_checks + additional_checks + type_specific_checks + app_specific_checks + issue_specific_checks
        
        return all_checks
    
    def get_certification_details(self, certifications, features):
        """
        Get detailed certification requirements.
        
        Args:
            certifications: List of predicted certifications
            features: Detected PCB features
            
        Returns:
            dict: Certification details and requirements
        """
        cert_details = {}
        pcb_type = features["pcb_type"]
        application = features.get("application", "")
        
        for cert in certifications:
            if cert == "CE":
                cert_details["CE"] = {
                    "description": "European Conformity - Required for products sold in EU",
                    "requirements": [
                        "EMC Directive compliance",
                        "RoHS compliance",
                        "Safety testing",
                        "Technical documentation"
                    ]
                }
                # Add PCB-specific requirements
                if pcb_type == "high_frequency":
                    cert_details["CE"]["requirements"].append("RF emissions testing")
                if "medical" in application:
                    cert_details["CE"]["requirements"].append("Medical Device Directive compliance")
                
            elif cert == "RoHS":
                cert_details["RoHS"] = {
                    "description": "Restriction of Hazardous Substances - Environmental standard",
                    "requirements": [
                        "No lead, mercury, cadmium, hexavalent chromium, PBBs, PBDEs",
                        "Test reports for materials",
                        "Declaration of Conformity"
                    ]
                }
                # Add PCB-specific requirements
                if pcb_type in ["flexible", "rigid_flex"]:
                    cert_details["RoHS"]["requirements"].append("Special testing for flexible materials")
                
            elif cert == "UL":
                cert_details["UL"] = {
                    "description": "Underwriters Laboratories - Safety standard",
                    "requirements": [
                        "Safety testing",
                        "Flammability testing",
                        "Regular factory audits",
                        "UL mark application"
                    ]
                }
                # Add PCB-specific requirements
                if pcb_type == "high_power":
                    cert_details["UL"]["requirements"].append("High-voltage clearance verification")
                    cert_details["UL"]["requirements"].append("Thermal endurance testing")
                
            elif cert == "FCC":
                cert_details["FCC"] = {
                    "description": "Federal Communications Commission - US EMC standard",
                    "requirements": [
                        "EMI/EMC testing",
                        "Radiated and conducted emissions testing",
                        "Technical documentation",
                        "FCC Declaration of Conformity or Certification"
                    ]
                }
                # Add PCB-specific requirements
                if pcb_type == "high_frequency":
                    cert_details["FCC"]["requirements"].append("Specific RF emissions profile testing")
                
            elif cert == "ISO9001":
                cert_details["ISO9001"] = {
                    "description": "Quality Management System standard",
                    "requirements": [
                        "Documented quality procedures",
                        "Regular audits",
                        "Continual improvement processes",
                        "Management reviews"
                    ]
                }
                
            elif cert == "IEC60950":
                cert_details["IEC60950"] = {
                    "description": "Information Technology Equipment Safety",
                    "requirements": [
                        "Electrical safety testing",
                        "Thermal testing",
                        "Mechanical strength testing",
                        "Fire enclosure requirements"
                    ]
                }
                
            elif cert == "IATF16949":
                cert_details["IATF16949"] = {
                    "description": "Automotive Quality Management System",
                    "requirements": [
                        "Automotive-specific quality processes",
                        "Production part approval process (PPAP)",
                        "Failure mode and effects analysis (FMEA)",
                        "Statistical process control"
                    ]
                }
                
            elif cert == "ISO13485":
                cert_details["ISO13485"] = {
                    "description": "Medical Device Quality Management System",
                    "requirements": [
                        "Risk management",
                        "Special process validation",
                        "Regulatory compliance documentation",
                        "Traceability requirements"
                    ]
                }
                
            elif cert == "DO-254":
                cert_details["DO-254"] = {
                    "description": "Design Assurance for Airborne Electronic Hardware",
                    "requirements": [
                        "Formal design process documentation",
                        "Requirements traceability",
                        "Extensive verification and validation",
                        "Configuration management"
                    ]
                }
                
            elif cert == "MIL-STD-883":
                cert_details["MIL-STD-883"] = {
                    "description": "Military Standard for Test Methods and Procedures for Microelectronics",
                    "requirements": [
                        "Extended environmental testing",
                        "Reliability demonstration",
                        "Detailed failure analysis",
                        "Stringent quality control procedures"
                    ]
                }
                
        return cert_details
    
    def format_details(self, results, features, analysis_option):
        """
        Format all details for display.
        
        Args:
            results: Analysis results
            features: Detected PCB features
            analysis_option: Analysis option selected
            
        Returns:
            str: Formatted details
        """
        details = []
        
        # Add PCB features
        details.append(f"PCB Type: {features['pcb_type'].upper()}")
        details.append(f"Component Density: {features['component_density'].capitalize()}")
        details.append(f"Estimated Layer Count: {features['estimated_layer_count']}")
        
        # Add application
        if "application" in features:
            details.append(f"Likely Application: {features['application'].replace('_', ' ').title()}")
        
        # Add detected issues
        if features['issues'] and features['issues'][0] != "none detected":
            details.append("Detected Issues: " + ", ".join(features['issues']))
        else:
            details.append("Detected Issues: None")
            
        details.append("\n")
            
        # Add quality check details
        if analysis_option in [1, 2] and "quality_details" in results:
            details.append("RECOMMENDED QUALITY CHECKS:")
            for i, check in enumerate(results["quality_details"], 1):
                details.append(f"{i}. {check}")
            details.append("\n")
            
        # Add certification details
        if analysis_option in [1, 3] and "certification_details" in results:
            if results["certification_details"]:
                details.append("CERTIFICATION REQUIREMENTS:")
                for cert, info in results["certification_details"].items():
                    details.append(f"• {cert}: {info['description']}")
                    details.append("  Requirements:")
                    for req in info['requirements']:
                        details.append(f"  - {req}")
                    details.append("")
            else:
                details.append("CERTIFICATION REQUIREMENTS: None specifically detected")
                
        return "\n".join(details)


# Function to use in Streamlit app
def analyze_pcb_image(image_bytes, analysis_option):
    """
    Analyze a PCB image.
    
    Args:
        image_bytes (bytes): The raw bytes of the uploaded image.
        analysis_option (int): The selected analysis option (1, 2, or 3).
        
    Returns:
        dict: A dictionary containing the analysis results.
    """
    analyzer = PCBAnalyzer()
    return analyzer.analyze_image(image_bytes, analysis_option)
