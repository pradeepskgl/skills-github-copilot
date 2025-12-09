"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_activities(self):
        """Test that GET /activities returns expected activities"""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Society",
            "Math Olympiad",
            "Science Club"
        ]
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_for_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_signup_adds_participant(self):
        """Test that signup adds participant to activity"""
        test_email = "pytest_test1@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Signup
        client.post(
            f"/activities/Chess%20Club/signup?email={test_email}"
        )
        
        # Check participant count increased
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert test_email in response.json()["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with duplicate email returns 400"""
        test_email = "pytest_test2@mergington.edu"
        
        # First signup
        client.post(
            f"/activities/Programming%20Class/signup?email={test_email}"
        )
        
        # Duplicate signup
        response = client.post(
            f"/activities/Programming%20Class/signup?email={test_email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_when_activity_full_returns_400(self):
        """Test that signing up to a full activity returns 400"""
        # First, get an activity with few spots
        response = client.get("/activities")
        activities = response.json()
        
        # Find or create a full activity by signing up max participants
        # For this test, we'll use Basketball Club which has 15 max participants
        activity_name = "Basketball Club"
        
        # Sign up emails until full
        for i in range(15):
            email = f"pytest_full_{i}@mergington.edu"
            response = client.post(
                f"/activities/Basketball%20Club/signup?email={email}"
            )
            # Some might already be registered, that's ok
        
        # Try to signup when full
        response = client.post(
            "/activities/Basketball%20Club/signup?email=pytest_overfull@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from activity"""
        test_email = "pytest_unregister@mergington.edu"
        activity_name = "Art Club"
        
        # Signup
        client.post(
            f"/activities/Art%20Club/signup?email={test_email}"
        )
        
        # Verify participant is added
        response = client.get("/activities")
        assert test_email in response.json()[activity_name]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/Art%20Club/unregister?email={test_email}"
        )
        assert response.status_code == 200
        
        # Verify participant is removed
        response = client.get("/activities")
        assert test_email not in response.json()[activity_name]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_unregistered_email_returns_400(self):
        """Test unregistering an email not in activity returns 400"""
        response = client.delete(
            "/activities/Drama%20Society/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_returns_success_message(self):
        """Test that unregister returns success message"""
        test_email = "pytest_unregister_msg@mergington.edu"
        
        # Signup first
        client.post(
            f"/activities/Drama%20Society/signup?email={test_email}"
        )
        
        # Unregister
        response = client.delete(
            f"/activities/Drama%20Society/unregister?email={test_email}"
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
