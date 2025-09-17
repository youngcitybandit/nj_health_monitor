#!/usr/bin/env python3
"""
Deploy NJ Health Monitor to Google Cloud Run with Cloud Scheduler
"""

import os
import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudRunDeployer:
    def __init__(self):
        self.project_id = None
        self.service_name = "nj-health-monitor"
        self.region = "us-central1"
        self.image_name = f"gcr.io/{{project_id}}/{self.service_name}"
        
    def check_prerequisites(self):
        """Check if required tools are installed."""
        logger.info("Checking prerequisites...")
        
        # Check if gcloud is installed
        try:
            result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
            logger.info("✅ Google Cloud SDK is installed")
        except FileNotFoundError:
            logger.error("❌ Google Cloud SDK not found. Please install: https://cloud.google.com/sdk/docs/install")
            return False
            
        # Check if Docker is installed
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            logger.info("✅ Docker is installed")
        except FileNotFoundError:
            logger.error("❌ Docker not found. Please install Docker Desktop")
            return False
            
        return True
    
    def setup_project(self):
        """Setup Google Cloud project."""
        logger.info("Setting up Google Cloud project...")
        
        # Get current project
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            self.project_id = result.stdout.strip()
            logger.info(f"✅ Using project: {self.project_id}")
        else:
            logger.error("❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID")
            return False
            
        self.image_name = f"gcr.io/{self.project_id}/{self.service_name}"
        return True
    
    def enable_apis(self):
        """Enable required Google Cloud APIs."""
        logger.info("Enabling required APIs...")
        
        apis = [
            'run.googleapis.com',
            'cloudbuild.googleapis.com',
            'cloudscheduler.googleapis.com',
            'containerregistry.googleapis.com'
        ]
        
        for api in apis:
            logger.info(f"Enabling {api}...")
            subprocess.run(['gcloud', 'services', 'enable', api], check=True)
        
        logger.info("✅ APIs enabled")
    
    def build_and_push_image(self):
        """Build and push Docker image."""
        logger.info("Building and pushing Docker image...")
        
        # Build with Cloud Build (handles the heavy lifting)
        cmd = [
            'gcloud', 'builds', 'submit',
            '--tag', self.image_name,
            '.'
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            logger.info("✅ Image built and pushed successfully")
            return True
        else:
            logger.error("❌ Image build failed")
            return False
    
    def deploy_cloud_run(self):
        """Deploy to Cloud Run."""
        logger.info("Deploying to Cloud Run...")
        
        cmd = [
            'gcloud', 'run', 'deploy', self.service_name,
            '--image', self.image_name,
            '--region', self.region,
            '--platform', 'managed',
            '--allow-unauthenticated',
            '--memory', '1Gi',
            '--cpu', '1',
            '--timeout', '900',
            '--max-instances', '1',
            '--set-env-vars', 'PYTHONUNBUFFERED=1'
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            logger.info("✅ Cloud Run service deployed successfully")
            return True
        else:
            logger.error("❌ Cloud Run deployment failed")
            return False
    
    def get_service_url(self):
        """Get the Cloud Run service URL."""
        cmd = [
            'gcloud', 'run', 'services', 'describe', self.service_name,
            '--region', self.region,
            '--format', 'value(status.url)'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    
    def setup_cloud_scheduler(self):
        """Setup Cloud Scheduler jobs."""
        logger.info("Setting up Cloud Scheduler...")
        
        service_url = self.get_service_url()
        if not service_url:
            logger.error("❌ Could not get service URL")
            return False
        
        # Create scheduler jobs for 9 AM and 2 PM EST
        jobs = [
            {
                'name': 'nj-health-check-morning',
                'schedule': '0 14 * * *',  # 9 AM EST = 14:00 UTC
                'description': 'Morning check for NJ health violations'
            },
            {
                'name': 'nj-health-check-afternoon', 
                'schedule': '0 19 * * *',  # 2 PM EST = 19:00 UTC
                'description': 'Afternoon check for NJ health violations'
            }
        ]
        
        for job in jobs:
            logger.info(f"Creating scheduler job: {job['name']}")
            
            cmd = [
                'gcloud', 'scheduler', 'jobs', 'create', 'http', job['name'],
                '--schedule', job['schedule'],
                '--uri', f"{service_url}/check",
                '--http-method', 'POST',
                '--location', self.region,
                '--description', job['description']
            ]
            
            # Delete existing job if it exists
            subprocess.run([
                'gcloud', 'scheduler', 'jobs', 'delete', job['name'],
                '--location', self.region, '--quiet'
            ], capture_output=True)
            
            result = subprocess.run(cmd)
            if result.returncode == 0:
                logger.info(f"✅ Scheduler job {job['name']} created")
            else:
                logger.error(f"❌ Failed to create job {job['name']}")
                return False
        
        logger.info("✅ Cloud Scheduler setup complete")
        return True
    
    def deploy(self):
        """Run the full deployment."""
        logger.info("🚀 Starting Cloud Run deployment...")
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Setting up project", self.setup_project),
            ("Enabling APIs", self.enable_apis),
            ("Building and pushing image", self.build_and_push_image),
            ("Deploying to Cloud Run", self.deploy_cloud_run),
            ("Setting up Cloud Scheduler", self.setup_cloud_scheduler)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
        
        service_url = self.get_service_url()
        
        logger.info("\n🎉 Deployment completed successfully!")
        logger.info("=" * 50)
        logger.info(f"Service URL: {service_url}")
        logger.info(f"Health check: {service_url}/")
        logger.info(f"Manual test: {service_url}/test")
        logger.info("\n📅 Scheduled runs:")
        logger.info("• 9:00 AM EST (14:00 UTC) daily")
        logger.info("• 2:00 PM EST (19:00 UTC) daily")
        logger.info("\n💰 Cost: ~$0.01-0.10 per day (only charged when running)")
        
        return True

if __name__ == "__main__":
    deployer = CloudRunDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n✅ Your PolicyEdge AI agent is now running on Google Cloud!")
        print("🎯 It will automatically check for violations twice daily")
        print("📧 And send personalized emails to facility administrators")
    else:
        print("\n❌ Deployment failed. Please check the logs above.")
