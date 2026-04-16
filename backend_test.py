import requests
import sys
import json
from datetime import datetime

class KonekteAPITester:
    def __init__(self, base_url="https://konekte-talent-scout.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_lead_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test GET /api/ root endpoint"""
        success, response = self.run_test(
            "Root endpoint",
            "GET",
            "",
            200
        )
        if success and response.get('message') == "Konekte AI Recruiter Agent API":
            print("   ✓ Correct message returned")
            return True
        elif success:
            print(f"   ⚠️ Unexpected message: {response.get('message')}")
        return success

    def test_get_leads_empty(self):
        """Test GET /api/leads returns empty array initially"""
        success, response = self.run_test(
            "Get leads (empty)",
            "GET",
            "leads",
            200
        )
        if success and isinstance(response, list):
            print(f"   ✓ Returns array with {len(response)} leads")
            return True
        return success

    def test_get_stats_initial(self):
        """Test GET /api/leads/stats returns correct initial stats"""
        success, response = self.run_test(
            "Get stats (initial)",
            "GET",
            "leads/stats",
            200
        )
        if success and isinstance(response, dict):
            expected_keys = ['total', 'by_status', 'by_platform', 'avg_score', 'high_potential', 'medium_potential', 'low_potential']
            has_all_keys = all(key in response for key in expected_keys)
            if has_all_keys:
                print(f"   ✓ All required keys present")
                print(f"   ✓ Total: {response.get('total')}, Avg Score: {response.get('avg_score')}")
                return True
            else:
                missing = [key for key in expected_keys if key not in response]
                print(f"   ⚠️ Missing keys: {missing}")
        return success

    def test_analyze_profile(self):
        """Test POST /api/analyze-profile with valid profile data"""
        profile_data = {
            "name": "Marie Dupont",
            "bio": "Professeure de mathematiques passionnee, je cree des videos educatives pour aider les etudiants",
            "platform": "youtube",
            "followers": 15000,
            "content_example": "Tutoriels de maths niveau lycee, exercices corriges"
        }
        
        success, response = self.run_test(
            "Analyze profile",
            "POST",
            "analyze-profile",
            200,
            data=profile_data
        )
        
        if success and isinstance(response, dict):
            required_fields = ['id', 'name', 'bio', 'platform', 'followers', 'content_example', 
                             'is_educator', 'domain', 'potential', 'score', 'reasoning', 
                             'generated_message', 'status', 'created_at']
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                print(f"   ✓ All required fields present")
                print(f"   ✓ Lead ID: {response.get('id')}")
                print(f"   ✓ Is Educator: {response.get('is_educator')}")
                print(f"   ✓ Score: {response.get('score')}")
                print(f"   ✓ Domain: {response.get('domain')}")
                print(f"   ✓ Status: {response.get('status')}")
                self.created_lead_id = response.get('id')
                return True
            else:
                missing = [field for field in required_fields if field not in response]
                print(f"   ⚠️ Missing fields: {missing}")
        return success

    def test_get_leads_after_creation(self):
        """Test GET /api/leads returns the created lead"""
        success, response = self.run_test(
            "Get leads (after creation)",
            "GET",
            "leads",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            lead = response[0]
            if lead.get('id') == self.created_lead_id:
                print(f"   ✓ Created lead found in list")
                print(f"   ✓ Lead name: {lead.get('name')}")
                return True
            else:
                print(f"   ⚠️ Created lead not found in list")
        return success

    def test_get_stats_after_creation(self):
        """Test GET /api/leads/stats returns updated stats"""
        success, response = self.run_test(
            "Get stats (after creation)",
            "GET",
            "leads/stats",
            200
        )
        if success and isinstance(response, dict):
            total = response.get('total', 0)
            if total > 0:
                print(f"   ✓ Total leads updated: {total}")
                print(f"   ✓ Average score: {response.get('avg_score')}")
                return True
            else:
                print(f"   ⚠️ Total still 0 after lead creation")
        return success

    def test_update_status_contacted(self):
        """Test PATCH /api/leads/{id}/status updates to contacted"""
        if not self.created_lead_id:
            print("   ⚠️ No lead ID available for status update")
            return False
            
        success, response = self.run_test(
            "Update status to contacted",
            "PATCH",
            f"leads/{self.created_lead_id}/status",
            200,
            data={"status": "contacted"}
        )
        if success and response.get('status') == 'contacted':
            print(f"   ✓ Status updated successfully")
            return True
        return success

    def test_update_status_replied(self):
        """Test PATCH /api/leads/{id}/status updates to replied"""
        if not self.created_lead_id:
            print("   ⚠️ No lead ID available for status update")
            return False
            
        success, response = self.run_test(
            "Update status to replied",
            "PATCH",
            f"leads/{self.created_lead_id}/status",
            200,
            data={"status": "replied"}
        )
        if success and response.get('status') == 'replied':
            print(f"   ✓ Status updated successfully")
            return True
        return success

    def test_regenerate_message(self):
        """Test POST /api/leads/{id}/regenerate-message"""
        if not self.created_lead_id:
            print("   ⚠️ No lead ID available for message regeneration")
            return False
            
        success, response = self.run_test(
            "Regenerate message",
            "POST",
            f"leads/{self.created_lead_id}/regenerate-message",
            200
        )
        if success and 'message' in response:
            print(f"   ✓ Message regenerated successfully")
            print(f"   ✓ New message length: {len(response.get('message', ''))}")
            return True
        return success

    def test_delete_lead(self):
        """Test DELETE /api/leads/{id}"""
        if not self.created_lead_id:
            print("   ⚠️ No lead ID available for deletion")
            return False
            
        success, response = self.run_test(
            "Delete lead",
            "DELETE",
            f"leads/{self.created_lead_id}",
            200
        )
        if success and response.get('message') == 'Lead deleted':
            print(f"   ✓ Lead deleted successfully")
            return True
        return success

    def test_filtering(self):
        """Test filtering functionality"""
        # Test status filter
        success1, _ = self.run_test(
            "Filter by status",
            "GET",
            "leads",
            200,
            params={"status": "new"}
        )
        
        # Test platform filter
        success2, _ = self.run_test(
            "Filter by platform",
            "GET",
            "leads",
            200,
            params={"platform": "youtube"}
        )
        
        # Test score filter
        success3, _ = self.run_test(
            "Filter by score range",
            "GET",
            "leads",
            200,
            params={"min_score": 50, "max_score": 100}
        )
        
        return success1 and success2 and success3

def main():
    print("🚀 Starting Konekte AI Recruiter Agent API Tests")
    print("=" * 60)
    
    tester = KonekteAPITester()
    
    # Run all tests in sequence
    tests = [
        tester.test_root_endpoint,
        tester.test_get_leads_empty,
        tester.test_get_stats_initial,
        tester.test_analyze_profile,  # This may take a few seconds due to AI processing
        tester.test_get_leads_after_creation,
        tester.test_get_stats_after_creation,
        tester.test_update_status_contacted,
        tester.test_update_status_replied,
        tester.test_regenerate_message,  # This may take a few seconds due to AI processing
        tester.test_filtering,
        tester.test_delete_lead,
    ]
    
    print(f"\n📋 Running {len(tests)} test suites...")
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            tester.tests_run += 1
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())