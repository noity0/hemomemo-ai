"""
🚀 run_programming_education_training.py — EXECUTE 1-HOUR PROGRAMMING EDUCATION TRAINING
========================================================================================
This script runs the comprehensive programming education training for Hemomemo AI.
It trains the AI on thinking methodologies, coding practices, learning strategies, and code editing.

USAGE:
    python run_programming_education_training.py

QANOON: 100% local, no external AI platforms, no FFmpeg, no cloud dependencies.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime

def check_environment():
    """Check if we're in the correct Hemomemo AI directory"""
    required_paths = [
        'model',
        'brain', 
        'core',
        'data',
        'app'
    ]
    
    current_dir = os.getcwd()
    print(f"🔍 Current directory: {current_dir}")
    
    missing_paths = []
    for path in required_paths:
        if not os.path.exists(path):
            missing_paths.append(path)
    
    if missing_paths:
        print(f"❌ Missing required paths: {missing_paths}")
        print("❌ Please run this script from the Hemomemo AI root directory (D:\\DigitalBrain)")
        return False
    
    print("✅ Environment check passed - Hemomemo AI directory detected")
    return True

def install_requirements():
    """Check and install required Python packages"""
    print("📦 Checking Python requirements...")
    
    try:
        # Check if requirements.txt exists
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            print("📋 Found requirements.txt")
            print("Requirements:")
            for line in requirements.strip().split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"  - {line}")
            
            # Install requirements
            print("🔧 Installing requirements...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Requirements installed successfully")
            else:
                print(f"⚠️  Warning: Some requirements may not have installed")
                print(f"   stderr: {result.stderr}")
        
        else:
            print("ℹ️  No requirements.txt found - proceeding with basic packages")
        
        # Check for essential packages
        essential_packages = ['numpy']
        for package in essential_packages:
            try:
                __import__(package)
                print(f"✅ {package} is available")
            except ImportError:
                print(f"❌ {package} is not available - installing...")
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                else:
                    print(f"❌ Failed to install {package}: {result.stderr}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements: {str(e)}")
        return False

def run_training():
    """Execute the programming education training"""
    print("\n🎓 Starting Programming Education Training...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Import and run the training module
        from programming_education import ProgrammingEducationTrainer
        
        print("🧠 Initializing Programming Education Trainer...")
        trainer = ProgrammingEducationTrainer()
        
        print("🚀 Starting training session...")
        print("This will train Hemomemo AI on:")
        print("  • Thinking methodologies for programming")
        print("  • Best coding practices and patterns")
        print("  • Effective learning strategies")
        print("  • Code editing and refactoring techniques")
        print()
        
        # Run the training
        results = trainer.train_hemomemo_ai()
        
        # Calculate training duration
        training_time = time.time() - start_time
        print(f"\n⏱️  Total training time: {training_time:.2f} seconds")
        print(f"⏱️  Average time per example: {training_time/len(trainer.training_data):.2f} seconds")
        
        # Save detailed training log
        training_log = {
            'training_session': 'programming_education',
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(time.time()).isoformat(),
            'duration_seconds': training_time,
            'results': results,
            'training_data_count': len(trainer.training_data),
            'categories': list(trainer.categories.keys())
        }
        
        log_path = os.path.join('data', 'training_logs', f'programming_education_{int(start_time)}.json')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(training_log, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Training log saved to: {log_path}")
        
        return results
        
    except ImportError as e:
        print(f"❌ Error importing training module: {str(e)}")
        print("❌ Make sure programming_education.py is in the correct location")
        return None
    except Exception as e:
        print(f"❌ Error during training: {str(e)}")
        return None

def verify_training():
    """Verify that the training was successful"""
    print("\n🔍 Verifying training results...")
    
    try:
        # Check if training data was added to the learner system
        from model.learner import STORE
        
        if os.path.exists(STORE):
            with open(STORE, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            programming_entries = [line for line in lines if 'programming_education_training' in line]
            
            if programming_entries:
                print(f"✅ Found {len(programming_entries)} programming education entries in training data")
                
                # Check categories
                categories_found = set()
                for line in programming_entries:
                    if '"category":' in line:
                        # Extract category from line
                        import re
                        match = re.search(r'"category":\s*"([^"]+)"', line)
                        if match:
                            categories_found.add(match.group(1))
                
                print(f"✅ Categories trained: {', '.join(categories_found)}")
                return True
            else:
                print("❌ No programming education entries found in training data")
                return False
        else:
            print("❌ Training data file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying training: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("🎯 HEMOMEMO AI PROGRAMMING EDUCATION TRAINING")
    print("=" * 60)
    print("📚 Training Module: 1-Hour Programming Education")
    print("🎓 Topics: Thinking, Coding, Learning, Code Editing")
    print("⏱️  Duration: Approximately 1 hour")
    print()
    
    # Step 1: Check environment
    if not check_environment():
        print("❌ Environment check failed. Exiting.")
        return False
    
    # Step 2: Install requirements
    if not install_requirements():
        print("❌ Requirements installation failed. Exiting.")
        return False
    
    # Step 3: Run training
    print("\n🚀 Starting training process...")
    training_results = run_training()
    
    if training_results is None:
        print("❌ Training failed. Exiting.")
        return False
    
    # Step 4: Verify training
    if verify_training():
        print("\n🎉 Training completed successfully!")
        print("✅ Hemomemo AI has been trained on programming education")
        print("✅ The AI can now help with:")
        print("   • Programming thinking methodologies")
        print("   • Best coding practices and patterns")
        print("   • Effective learning strategies")
        print("   • Code editing and refactoring techniques")
        return True
    else:
        print("\n⚠️  Training completed but verification failed")
        print("⚠️  The training may not have been fully applied")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)