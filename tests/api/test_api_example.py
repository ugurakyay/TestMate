import pytest
import requests
import json

class TestAPIExample:
    """Example API tests using requests"""
    
    def setup_method(self):
        """Setup test data before each test"""
        self.base_url = "https://jsonplaceholder.typicode.com"
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def test_get_posts(self):
        """Test GET request to retrieve posts"""
        response = requests.get(f"{self.base_url}/posts")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify response structure
        posts = response.json()
        assert isinstance(posts, list), "Response should be a list"
        assert len(posts) > 0, "Should return at least one post"
        
        # Verify post structure
        first_post = posts[0]
        assert 'id' in first_post, "Post should have 'id' field"
        assert 'title' in first_post, "Post should have 'title' field"
        assert 'body' in first_post, "Post should have 'body' field"
    
    def test_get_single_post(self):
        """Test GET request for a single post"""
        post_id = 1
        response = requests.get(f"{self.base_url}/posts/{post_id}")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify response data
        post = response.json()
        assert post['id'] == post_id, f"Post ID should be {post_id}"
        assert 'title' in post, "Post should have 'title' field"
        assert 'body' in post, "Post should have 'body' field"
    
    def test_create_post(self):
        """Test POST request to create a new post"""
        new_post = {
            'title': 'Test Post',
            'body': 'This is a test post',
            'userId': 1
        }
        
        response = requests.post(
            f"{self.base_url}/posts",
            headers=self.headers,
            data=json.dumps(new_post)
        )
        
        # Verify response status
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        
        # Verify response data
        created_post = response.json()
        assert created_post['title'] == new_post['title'], "Title should match"
        assert created_post['body'] == new_post['body'], "Body should match"
        assert 'id' in created_post, "Created post should have an ID"
    
    def test_update_post(self):
        """Test PUT request to update a post"""
        post_id = 1
        updated_data = {
            'id': post_id,
            'title': 'Updated Title',
            'body': 'Updated body content',
            'userId': 1
        }
        
        response = requests.put(
            f"{self.base_url}/posts/{post_id}",
            headers=self.headers,
            data=json.dumps(updated_data)
        )
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify response data
        updated_post = response.json()
        assert updated_post['title'] == updated_data['title'], "Title should be updated"
        assert updated_post['body'] == updated_data['body'], "Body should be updated"
    
    def test_delete_post(self):
        """Test DELETE request to delete a post"""
        post_id = 1
        response = requests.delete(f"{self.base_url}/posts/{post_id}")
        
        # Verify response status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}" 