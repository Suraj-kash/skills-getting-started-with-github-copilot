import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_success(self):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_get_activities_contains_expected_fields(self):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_contains_known_activities(self):
        """Test that expected activities are present"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "testuser@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        
        # Sign up for an activity
        response = client.post(
            "/activities/Swimming Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Swimming Club"]["participants"]
    
    def test_signup_duplicate_participant(self):
        """Test that signing up twice fails gracefully"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity(self):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_with_valid_email_format(self):
        """Test signup with different valid email formats"""
        emails = [
            "test.user@mergington.edu",
            "test+tag@mergington.edu",
            "simple@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                "/activities/Drama Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200


class TestRoot:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
    
    def test_root_redirect_follow(self):
        """Test that following the redirect works"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestActivityIntegration:
    """Integration tests for activity workflows"""
    
    def test_multiple_signups_same_activity(self):
        """Test multiple different students signing up for the same activity"""
        activity = "Science Club"
        emails = ["science1@mergington.edu", "science2@mergington.edu", "science3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for email in emails:
            assert email in activities[activity]["participants"]
    
    def test_student_signup_multiple_activities(self):
        """Test that a student can sign up for multiple different activities"""
        email = "multisport@mergington.edu"
        activities_to_join = ["Debate Team", "Basketball Team"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]
