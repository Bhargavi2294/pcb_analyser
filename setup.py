# setup.py
import os
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw
import json

def create_directory_structure():
    """Create the necessary directory structure for the project."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("dataset", exist_ok=True)
    
    # Create PCB type directories
    pcb_types = [
        "single_sided", "double_sided", "multilayer",
        "flexible", "rigid_flex", "high_frequency", "high_power"
    ]
    
    for pcb_type in pcb_types:
        os.makedirs(f"dataset/{pcb_type}", exist_ok=True)
        
    print("Directory structure created successfully!")

def create_sample_dataset():
    """Create a sample PCB dataset CSV file."""
    data = [
        ["PCB001", "dataset/single_sided/PCB001.jpg", "single_sided", "low", 1, "basic", "CE", "none", "consumer_electronics", "FR-4", "none"],
        ["PCB002", "dataset/single_sided/PCB002.jpg", "single_sided", "medium", 1, "enhanced", "CE;RoHS", "solder_bridge", "consumer_electronics", "FR-4", "none"],
        ["PCB003", "dataset/single_sided/PCB003.jpg", "single_sided", "low", 1, "basic", "CE", "open_circuit", "toys", "FR-4", "none"],
        ["PCB004", "dataset/double_sided/PCB004.jpg", "double_sided", "medium", 2, "enhanced", "CE;RoHS;UL", "none", "industrial_control", "FR-4", "none"],
        ["PCB005", "dataset/double_sided/PCB005.jpg", "double_sided", "high", 2, "comprehensive", "CE;RoHS;UL;FCC", "solder_quality", "medical_non_critical", "FR-4", "none"],
        ["PCB006", "dataset/multilayer/PCB006.jpg", "multilayer", "high", 4, "comprehensive", "CE;RoHS;UL;FCC", "none", "telecommunications", "FR-4", "impedance_control"],
        ["PCB007", "dataset/flexible/PCB007.jpg", "flexible", "medium", 2, "enhanced", "CE;RoHS;UL", "none", "wearables", "Polyimide", "flex_durability"]
    ]
    
    columns = [
        "image_id", "image_path", "pcb_type", "components_density", "layer_count", 
        "quality_check_required", "certification_needed", "defect_type", 
        "intended_application", "material_type", "special_features"
    ]
    
    df = pd.DataFrame(data, columns=columns)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/pcb_dataset.csv", index=False)
    print("Sample dataset CSV created successfully!")

def create_dummy_images():
    """Create dummy PCB images for demonstration."""
    try:
        df = pd.read_csv("data/pcb_dataset.csv")
    except FileNotFoundError:
        print("PCB dataset CSV not found. Creating it...")
        create_sample_dataset()
        df = pd.read_csv("data/pcb_dataset.csv")
    
    # Create a dummy image for each entry in the dataset
    for _, row in df.iterrows():
        image_path = row["image_path"]
        pcb_type = row["pcb_type"]
        components_density = row["components_density"]
        defect_type = row["defect_type"]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        # Create a colored rectangle as a dummy PCB
        img = Image.new('RGB', (224, 224), color=(150, 150, 150))
        draw = ImageDraw.Draw(img)
        
        # Draw different patterns based on PCB type
        if pcb_type == "single_sided":
            draw.rectangle([20, 20, 204, 204], fill=(130, 130, 130), outline=(200, 200, 200))
        elif pcb_type == "double_sided":
            draw.rectangle([20, 20, 204, 204], fill=(120, 120, 120), outline=(200, 200, 200))
            draw.rectangle([40, 40, 184, 184], fill=(140, 140, 140), outline=(180, 180, 180))
        elif pcb_type == "multilayer":
            draw.rectangle([20, 20, 204, 204], fill=(110, 110, 110), outline=(200, 200, 200))
            for i in range(3):
                inset = 20 + (i * 20)
                draw.rectangle(
                    [inset, inset, 224 - inset, 224 - inset],
                    outline=(180 - (i * 20), 180 - (i * 20), 180 - (i * 20))
                )
        elif pcb_type == "flexible":
            draw.rectangle([20, 20, 204, 204], fill=(150, 150, 100), outline=(200, 200, 150))
            # Add curved lines to represent flexibility
            for i in range(5):
                y = 50 + (i * 30)
                for x in range(30, 194, 2):
                    draw.point((x, y + int(10 * np.sin(x * 0.1))), fill=(180, 180, 130))
        else:
            # Default pattern
            draw.rectangle([20, 20, 204, 204], fill=(130, 130, 130), outline=(200, 200, 200))
        
        # Add "components" based on density
        num_components = {
            "low": 5,
            "medium": 15,
            "high": 30,
            "very_high": 50
        }.get(components_density, 10)
        
        # Add random "components"
        np.random.seed(int(row["image_id"].replace("PCB", "")))  # For reproducibility
        for _ in range(num_components):
            x, y = np.random.randint(30, 194, 2)
            size = np.random.randint(5, 15)
            color = tuple(np.random.randint(50, 150, 3))
            draw.rectangle([x, y, x + size, y + size], fill=color)
                
        # Save the image
        img.save(image_path)
        
    print(f"Created {len(df)} dummy PCB images!")

def create_dummy_models():
    """Create dummy model class names files for demonstration."""
    os.makedirs("models", exist_ok=True)
    
    # Create dummy model class names files
    quality_classes = ['basic', 'enhanced', 'comprehensive']
    with open("models/quality_check_classes.json", "w") as f:
        json.dump(quality_classes, f)
    
    cert_classes = ['CE', 'RoHS', 'UL', 'FCC', 'ISO9001', 'IEC60950', 'IATF16949']
    with open("models/certification_classes.json", "w") as f:
        json.dump(cert_classes, f)
    
    print("Created dummy model class files!")

if __name__ == "__main__":
    print("Setting up Mefron PCB Analyzer...")
    create_directory_structure()
    create_sample_dataset()
    create_dummy_images()
    create_dummy_models()
    print("Setup complete!")
