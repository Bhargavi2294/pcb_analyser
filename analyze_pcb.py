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
        self.cert_classes = ['CE', 'RoHS', 'UL', 'FCC', 'ISO9001', 'IEC60950', 'IATF16949']
        
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
                # Determine quality level based on detected features
                if features['component_density'] == 'high' or features['estimated_layer_count'] > 4:
                    quality_result = "comprehensive"
                elif features['component_density'] == 'medium':
                    quality_result = "enhanced"
                else:
                    quality_result = "basic"
                    
                results["quality_check_required"] = f"{quality_result} (simulated)"
                
                # Add quality check details
                quality_details = self.get_quality_check_details(quality_result, features)
                results["quality_details"] = quality_details
            
            # Certification prediction (option 1 or 3)
            if analysis_option in [1, 3]:
                # Determine certifications based on features
                predicted_certs = ["CE"]  # Basic certification for all
                
                if features['estimated_layer_count'] > 1:
                    predicted_certs.append("RoHS")
                    
                if features['component_density'] in ['medium', 'high']:
                    predicted_certs.append("UL")
                    
                if features['pcb_type'] in ['high_frequency', 'multilayer']:
                    predicted_certs.append("FCC")
                    
                cert_result = "; ".join([f"{cert} (simulated)" for cert in predicted_certs])
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
    
    def detect_pcb_features(self, image):
        """Detect features from a PCB image."""
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
            
        return {
            "pcb_type": pcb_type,
            "component_density": component_density,
            "estimated_layer_count": layer_count,
            "edge_density": edge_density,
            "issues": issues if issues else ["none detected"]
        }
    
    def get_quality_check_details(self, quality_level, features):
        """Get detailed quality check requirements."""
        pcb_type = features["pcb_type"]
        component_density = features["component_density"]
        issues = features["issues"]
        
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
            
        # Add issue-specific checks
        issue_specific_checks = []
        for issue in issues:
            if issue != "none detected":
                issue_specific_checks.append(f"Detailed inspection for {issue}")
                
        # Combine all checks
        all_checks = base_checks + additional_checks + type_specific_checks + issue_specific_checks
        
        return all_checks
    
    def get_certification_details(self, certifications, features):
        """Get detailed certification requirements."""
        cert_details = {}
        
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
            elif cert == "RoHS":
                cert_details["RoHS"] = {
                    "description": "Restriction of Hazardous Substances - Environmental standard",
                    "requirements": [
                        "No lead, mercury, cadmium, hexavalent chromium, PBBs, PBDEs",
                        "Test reports for materials",
                        "Declaration of Conformity"
                    ]
                }
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
                
        return cert_details
    
    def format_details(self, results, features, analysis_option):
        """Format all details for display."""
        details = []
        
        # Add PCB features
        details.append(f"PCB Type: {features['pcb_type'].upper()}")
        details.append(f"Component Density: {features['component_density'].capitalize()}")
        details.append(f"Estimated Layer Count: {features['estimated_layer_count']}")
        
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
    """Analyze a PCB image."""
    analyzer = PCBAnalyzer()
    return analyzer.analyze_image(image_bytes, analysis_option)
