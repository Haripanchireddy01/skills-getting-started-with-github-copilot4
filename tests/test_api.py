"""Tests for the Mergington High School API endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_root_redirects_to_static(client):
    """Test that the root endpoint redirects to the static index page"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    activities = response.json()
    assert isinstance(activities, dict)
    assert len(activities) > 0
    
    # Check structure of an activity
    for name, details in activities.items():
        assert "description" in details
        assert "schedule" in details
        assert "max_participants" in details
        assert "participants" in details
        assert isinstance(details["participants"], list)
        assert isinstance(details["max_participants"], int)


def test_get_activities_returns_all_expected_activities(client):
    """Test that all expected activities are returned"""
    response = client.get("/activities")
    activities = response.json()
    
    expected_activities = [
        "Soccer Team", "Basketball Team", "Art Club", 
        "Drama Club", "Debate Team", "Science Club",
        "Chess Club", "Programming Class", "Gym Class"
    ]
    
    for activity_name in expected_activities:
        assert activity_name in activities


def test_signup_for_activity_success(client, reset_activities):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "test@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client, reset_activities):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_participant(client, reset_activities):
    """Test that a participant cannot sign up for the same activity twice"""
    email = "duplicate@mergington.edu"
    activity = "Chess Club"
    
    # First signup should succeed
    response1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert response2.status_code == 400
    data = response2.json()
    assert "already signed up" in data["detail"].lower()


def test_remove_participant_success(client, reset_activities):
    """Test successfully removing a participant from an activity"""
    activity = "Chess Club"
    email = "michael@mergington.edu"
    
    # Verify participant exists
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Remove participant
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_remove_participant_from_nonexistent_activity(client, reset_activities):
    """Test removing a participant from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Activity/participants/test@mergington.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_remove_nonexistent_participant(client, reset_activities):
    """Test removing a participant who is not registered for the activity"""
    response = client.delete(
        "/activities/Chess Club/participants/nonexistent@mergington.edu"
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_signup_and_remove_workflow(client, reset_activities):
    """Test the complete workflow of signing up and then removing a participant"""
    activity = "Art Club"
    email = "workflow@mergington.edu"
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify signup
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity]["participants"]
    
    # Remove
    remove_response = client.delete(f"/activities/{activity}/participants/{email}")
    assert remove_response.status_code == 200
    
    # Verify removal
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity]["participants"]


def test_multiple_participants_same_activity(client, reset_activities):
    """Test that multiple different participants can sign up for the same activity"""
    activity = "Drama Club"
    emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
    
    for email in emails:
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    # Verify all participants were added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    for email in emails:
        assert email in activities[activity]["participants"]


def test_activity_name_with_spaces(client, reset_activities):
    """Test that activity names with spaces are handled correctly"""
    response = client.post(
        "/activities/Soccer Team/signup?email=spaces@mergington.edu"
    )
    assert response.status_code == 200


def test_participant_count_increases(client, reset_activities):
    """Test that participant count increases when signing up"""
    activity = "Science Club"
    
    # Get initial count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Add participant
    client.post(f"/activities/{activity}/signup?email=newuser@mergington.edu")
    
    # Get new count
    final_response = client.get("/activities")
    final_count = len(final_response.json()[activity]["participants"])
    
    assert final_count == initial_count + 1


def test_participant_count_decreases(client, reset_activities):
    """Test that participant count decreases when removing"""
    activity = "Basketball Team"
    email = "james@mergington.edu"
    
    # Get initial count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Remove participant
    client.delete(f"/activities/{activity}/participants/{email}")
    
    # Get new count
    final_response = client.get("/activities")
    final_count = len(final_response.json()[activity]["participants"])
    
    assert final_count == initial_count - 1
