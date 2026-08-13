import os
import subprocess
import zipfile

def download_and_extract_kaggle_data(competition_name, output_dir):
    """
    Downloads data from a Kaggle competition and extracts it to the given directory.
    Requires the 'kaggle' python package to be installed and 'kaggle.json' to be present
    in ~/.kaggle/.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Downloading data for competition: {competition_name}...")
    try:
        # Use subprocess to call the kaggle CLI
        # This requires the kaggle package to be installed (pip install kaggle)
        subprocess.run(
            ['kaggle', 'competitions', 'download', '-c', competition_name, '-p', output_dir],
            check=True
        )
        print("Download successful.")

        # Look for the downloaded zip file
        zip_path = os.path.join(output_dir, f"{competition_name}.zip")
        if os.path.exists(zip_path):
            print(f"Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            print("Extraction complete.")
            os.remove(zip_path) # Clean up zip file
        else:
            print("No zip file found to extract. Files may have been downloaded uncompressed.")

    except subprocess.CalledProcessError as e:
        print(f"Error downloading data: {e}")
        print("Please ensure you have the 'kaggle' pip package installed and your kaggle.json credentials are set up correctly.")
    except FileNotFoundError:
        print("The 'kaggle' command was not found. Please install it using 'pip install kaggle'.")

if __name__ == "__main__":
    COMPETITION = "liquidity-arena-ai-quant-trading-competition"
    OUTPUT_DIR = "data/raw"
    download_and_extract_kaggle_data(COMPETITION, OUTPUT_DIR)
