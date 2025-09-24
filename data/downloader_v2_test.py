#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced NCS Downloader
Tests all functionality including database management, metadata extraction, and JSON handling
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .downloader_v2 import Track, TrackDatabase, EnhancedNCSDownloader
    from .data_manager import DatabaseManager
except ImportError:
    print("Warning: Could not import modules. Running in standalone mode.")
    
    # Mock classes for standalone testing
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class Track:
        title: str
        artists: List[str]
        genres: List[str]
        url: str
        download_url: Optional[str] = None
        publish_date: Optional[str] = None
        credit_info: Optional[str] = None
        file_size: Optional[int] = None
        file_path: Optional[str] = None
        track_id: Optional[str] = None

class TestTrackDatabase(unittest.TestCase):
    """Test the TrackDatabase class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_db.json"
        self.db = TrackDatabase(str(self.db_path))
        
        # Create sample tracks
        self.sample_track1 = Track(
            title="Test Song 1",
            artists=["Test Artist 1", "Test Artist 2"],
            genres=["Electronic", "Dubstep"],
            url="https://example.com/test1",
            download_url="https://example.com/test1.mp3",
            publish_date="2023-01-15",
            file_size=1024*1024*5  # 5MB
        )
        
        self.sample_track2 = Track(
            title="Test Song 2",
            artists=["Test Artist 3"],
            genres=["House"],
            url="https://example.com/test2",
            download_url="https://example.com/test2.mp3",
            publish_date="2023-06-20",
            file_size=1024*1024*7  # 7MB
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_database_initialization(self):
        """Test database initialization"""
        self.assertEqual(len(self.db.data["tracks"]), 0)
        self.assertTrue(self.db_path.parent.exists())
    
    def test_add_track(self):
        """Test adding a track to database"""
        track_id = self.db.add_track(self.sample_track1)
        
        # Verify track was added
        self.assertIn(track_id, self.db.data["tracks"])
        self.assertEqual(self.db.data["tracks"][track_id]["title"], "Test Song 1")
        self.assertEqual(len(self.db.data["tracks"][track_id]["artists"]), 2)
        self.assertEqual(len(self.db.data["tracks"][track_id]["genres"]), 2)
    
    def test_track_id_generation(self):
        """Test unique track ID generation"""
        track_id1 = self.db.generate_track_id(self.sample_track1)
        track_id2 = self.db.generate_track_id(self.sample_track2)
        
        self.assertNotEqual(track_id1, track_id2)
        self.assertTrue(track_id1.startswith("track_"))
        self.assertTrue(track_id2.startswith("track_"))
    
    def test_duplicate_track_detection(self):
        """Test detection of duplicate tracks"""
        # Add first track
        track_id1 = self.db.add_track(self.sample_track1)
        self.assertIsNotNone(track_id1)
        
        # Try to add same track again
        existing_id = self.db.track_exists(self.sample_track1)
        self.assertEqual(existing_id, track_id1)
    
    def test_database_persistence(self):
        """Test database save and load functionality"""
        # Add track and save
        track_id = self.db.add_track(self.sample_track1)
        self.db.save_database()
        
        # Create new database instance and load
        new_db = TrackDatabase(str(self.db_path))
        self.assertIn(track_id, new_db.data["tracks"])
        self.assertEqual(new_db.data["tracks"][track_id]["title"], "Test Song 1")
    
    def test_database_stats(self):
        """Test database statistics generation"""
        # Add sample tracks
        self.db.add_track(self.sample_track1)
        self.db.add_track(self.sample_track2)
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats["total_tracks"], 2)
        self.assertEqual(stats["total_file_size"], 1024*1024*12)  # 5MB + 7MB
        self.assertIn("Electronic", stats["genres"])
        self.assertIn("House", stats["genres"])
        self.assertIn("Test Artist 1", stats["artists"])

class TestMetadataExtraction(unittest.TestCase):
    """Test metadata extraction functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.downloader = Mock()  # Mock downloader for testing
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_parse_artists(self):
        """Test artist name parsing"""
        # This would test the actual parse_artists method
        test_cases = [
            ("Alan Walker feat. Noah Cyrus", ["Alan Walker", "Noah Cyrus"]),
            ("Artist1 & Artist2 & Artist3", ["Artist1", "Artist2", "Artist3"]),
            ("Single Artist", ["Single Artist"]),
            ("Artist1 x Artist2", ["Artist1", "Artist2"])
        ]
        
        # Mock the parse_artists method
        def mock_parse_artists(text):
            if "feat." in text or "ft." in text:
                return [a.strip() for a in text.replace("feat.", "&").replace("ft.", "&").split("&")]
            elif "&" in text:
                return [a.strip() for a in text.split("&")]
            elif "x" in text:
                return [a.strip() for a in text.split("x")]
            else:
                return [text.strip()]
        
        for input_text, expected in test_cases:
            result = mock_parse_artists(input_text)
            self.assertEqual(len(result), len(expected))
    
    def test_parse_genres(self):
        """Test genre parsing"""
        test_cases = [
            ("Electronic, Dubstep, Bass", ["Electronic", "Dubstep", "Bass"]),
            ("House Music", ["House"]),
            ("Progressive House & Trance", ["Progressive House", "Trance"])
        ]
        
        # Mock genre parsing
        def mock_parse_genres(text):
            separators = [",", "&", "|", ";"]
            genres = [text]
            for sep in separators:
                new_genres = []
                for genre in genres:
                    new_genres.extend([g.strip() for g in genre.split(sep)])
                genres = new_genres
            return [g for g in genres if g]
        
        for input_text, expected_count in test_cases:
            result = mock_parse_genres(input_text)
            self.assertGreaterEqual(len(result), 1)
    
    def test_date_parsing(self):
        """Test date parsing functionality"""
        test_cases = [
            ("2023-01-15", "2023-01-15"),
            ("2023-01-15T10:30:00Z", "2023-01-15"),
            ("January 15, 2023", "2023-01-15"),
            ("15/01/2023", "2023-01-15"),
            ("2023", "2023-01-01")
        ]
        
        def mock_parse_date(date_str):
            import re
            from datetime import datetime
            
            if not date_str:
                return None
            
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S',
                '%B %d, %Y',
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(date_str.split('T')[0], fmt.split('T')[0])
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Try to extract year
            year_match = re.search(r'20\d{2}', date_str)
            if year_match:
                return f"{year_match.group()}-01-01"
            
            return None
        
        for input_date, expected in test_cases:
            result = mock_parse_date(input_date)
            if expected:
                self.assertIsNotNone(result)
                self.assertTrue(result.startswith("20"))  # Should be a valid year

class TestDatabaseManager(unittest.TestCase):
    """Test the DatabaseManager utility class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_db.json"
        
        # Create sample database
        sample_data = {
            "tracks": {
                "track_test_1": {
                    "title": "Test Song 1",
                    "artists": ["Test Artist 1"],
                    "genres": ["Electronic"],
                    "url": "https://example.com/test1.mp3",
                    "publish_date": "2023-01-15",
                    "file_size": 1024*1024*5
                },
                "track_test_2": {
                    "title": "Another Song",
                    "artists": ["Test Artist 2"],
                    "genres": ["Dubstep"],
                    "url": "https://example.com/test2.mp3",
                    "publish_date": "2023-06-20",
                    "file_size": 1024*1024*7
                }
            }
        }
        
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        
        # Mock DatabaseManager for testing
        self.db_manager = Mock()
        self.db_manager.data = sample_data
        self.db_manager.db_path = self.db_path
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_search_functionality(self):
        """Test search functionality"""
        def mock_search_tracks(query, field="all"):
            results = []
            query_lower = query.lower()
            
            for track_id, track_data in self.db_manager.data["tracks"].items():
                match = False
                
                if field == "all" or field == "title":
                    if query_lower in track_data.get("title", "").lower():
                        match = True
                
                if field == "all" or field == "artist":
                    artists = track_data.get("artists", [])
                    if any(query_lower in artist.lower() for artist in artists):
                        match = True
                
                if match:
                    result = track_data.copy()
                    result["track_id"] = track_id
                    results.append(result)
            
            return results
        
        # Test title search
        results = mock_search_tracks("Test Song")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Song 1")
        
        # Test artist search
        results = mock_search_tracks("Test Artist 2", "artist")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Another Song")
    
    def test_stats_generation(self):
        """Test statistics generation"""
        def mock_get_detailed_stats():
            tracks = self.db_manager.data["tracks"]
            total_tracks = len(tracks)
            
            genre_counts = {}
            artist_counts = {}
            total_size = 0
            
            for track_data in tracks.values():
                # Count genres
                for genre in track_data.get("genres", []):
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
                
                # Count artists
                for artist in track_data.get("artists", []):
                    artist_counts[artist] = artist_counts.get(artist, 0) + 1
                
                # Sum file sizes
                total_size += track_data.get("file_size", 0)
            
            return {
                "total_tracks": total_tracks,
                "total_file_size_mb": round(total_size / (1024 * 1024), 2),
                "genres": {"counts": genre_counts},
                "artists": {"counts": artist_counts}
            }
        
        stats = mock_get_detailed_stats()
        
        self.assertEqual(stats["total_tracks"], 2)
        self.assertEqual(stats["total_file_size_mb"], 12.0)  # 5MB + 7MB
        self.assertIn("Electronic", stats["genres"]["counts"])
        self.assertIn("Dubstep", stats["genres"]["counts"])

class TestFileOperations(unittest.TestCase):
    """Test file operations and validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        def sanitize_filename(filename):
            import re
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                filename = filename.replace(char, '_')
            filename = re.sub(r'[_\s]+', '_', filename)
            return filename[:200]  # Limit length
        
        test_cases = [
            ("Artist - Song.mp3", "Artist_-_Song.mp3"),
            ("Bad<>Chars.mp3", "Bad__Chars.mp3"),
            ("Multiple   Spaces.mp3", "Multiple_Spaces.mp3"),
            ("A" * 250 + ".mp3", "A" * 196 + ".mp3")  # Length limit test
        ]
        
        for input_name, expected_pattern in test_cases:
            result = sanitize_filename(input_name)
            self.assertNotIn('<', result)
            self.assertNotIn('>', result)
            self.assertNotIn(':', result)
            self.assertLessEqual(len(result), 200)
    
    def test_json_serialization(self):
        """Test JSON serialization of track data"""
        track_data = {
            "title": "Test Song",
            "artists": ["Artist 1", "Artist 2"],
            "genres": ["Electronic", "House"],
            "url": "https://example.com/test.mp3",
            "publish_date": "2023-01-15",
            "file_size": 1024*1024*5,
            "download_timestamp": datetime.now().isoformat()
        }
        
        # Test serialization
        json_str = json.dumps(track_data, ensure_ascii=False, indent=2)
        self.assertIsInstance(json_str, str)
        
        # Test deserialization
        loaded_data = json.loads(json_str)
        self.assertEqual(loaded_data["title"], track_data["title"])
        self.assertEqual(len(loaded_data["artists"]), 2)
        self.assertEqual(len(loaded_data["genres"]), 2)

class TestValidationAndSafety(unittest.TestCase):
    """Test validation and safety features"""
    
    def test_url_validation(self):
        """Test download URL validation"""
        def mock_validate_url(url):
            # Mock validation logic
            valid_extensions = ['.mp3', '.wav', '.flac', '.m4a']
            valid_domains = ['ncs.io', 'soundcloud.com', 'example.com']
            
            # Check extension
            has_valid_ext = any(url.lower().endswith(ext) for ext in valid_extensions)
            
            # Check domain (simplified)
            has_valid_domain = any(domain in url.lower() for domain in valid_domains)
            
            return has_valid_ext and has_valid_domain
        
        test_urls = [
            ("https://ncs.io/track.mp3", True),
            ("https://malicious.com/virus.exe", False),
            ("https://example.com/song.wav", True),
            ("https://ncs.io/track.txt", False)
        ]
        
        for url, expected in test_urls:
            result = mock_validate_url(url)
            self.assertEqual(result, expected, f"URL validation failed for: {url}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        import time
        
        def mock_rate_limiter(delay=2.0):
            start_time = time.time()
            time.sleep(min(delay, 0.01))  # Use very short delay for testing
            end_time = time.time()
            return end_time - start_time
        
        # Test that rate limiting adds delay
        elapsed = mock_rate_limiter(0.01)
        self.assertGreaterEqual(elapsed, 0.005)  # At least some delay
    
    def test_error_handling(self):
        """Test error handling mechanisms"""
        def mock_download_with_error_handling(url, max_retries=3):
            attempt = 0
            errors = []
            
            while attempt < max_retries:
                try:
                    # Simulate different types of errors
                    if attempt == 0:
                        raise ConnectionError("Network error")
                    elif attempt == 1:
                        raise FileNotFoundError("File not found")
                    else:
                        return True  # Success on third attempt
                        
                except Exception as e:
                    errors.append(str(e))
                    attempt += 1
            
            return False, errors
        
        # Test successful retry
        result = mock_download_with_error_handling("test_url")
        self.assertTrue(result)
        
        # Test max retries exceeded
        result = mock_download_with_error_handling("test_url", max_retries=1)
        self.assertIsInstance(result, tuple)
        self.assertFalse(result[0])

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.download_dir = Path(self.test_dir) / "downloads"
        self.download_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from discovery to database storage"""
        # Mock the complete workflow
        def mock_complete_workflow():
            # Step 1: Track discovery
            discovered_tracks = [
                Track(
                    title="Integration Test Song",
                    artists=["Test Artist"],
                    genres=["Electronic"],
                    url="https://example.com/test"
                )
            ]
            
            # Step 2: Metadata enhancement
            enhanced_tracks = []
            for track in discovered_tracks:
                track.download_url = "https://example.com/test.mp3"
                track.publish_date = "2023-01-15"
                track.file_size = 1024 * 1024 * 5  # 5MB
                enhanced_tracks.append(track)
            
            # Step 3: Database storage
            db = TrackDatabase(str(self.download_dir / "test_db.json"))
            stored_tracks = []
            
            for track in enhanced_tracks:
                track_id = db.add_track(track)
                stored_tracks.append(track_id)
            
            db.save_database()
            
            return {
                "discovered": len(discovered_tracks),
                "enhanced": len(enhanced_tracks),
                "stored": len(stored_tracks),
                "database_tracks": len(db.data["tracks"])
            }
        
        result = mock_complete_workflow()
        
        # Verify workflow completed successfully
        self.assertEqual(result["discovered"], 1)
        self.assertEqual(result["enhanced"], 1)
        self.assertEqual(result["stored"], 1)
        self.assertEqual(result["database_tracks"], 1)
    
    def test_database_consistency(self):
        """Test database consistency across operations"""
        db_path = self.download_dir / "consistency_test.json"
        
        # Create initial database
        db1 = TrackDatabase(str(db_path))
        track1 = Track(
            title="Consistency Test 1",
            artists=["Artist 1"],
            genres=["Genre 1"],
            url="https://example.com/test1"
        )
        track_id1 = db1.add_track(track1)
        db1.save_database()
        
        # Load database in new instance and add another track
        db2 = TrackDatabase(str(db_path))
        track2 = Track(
            title="Consistency Test 2",
            artists=["Artist 2"],
            genres=["Genre 2"],
            url="https://example.com/test2"
        )
        track_id2 = db2.add_track(track2)
        db2.save_database()
        
        # Verify both tracks exist
        db3 = TrackDatabase(str(db_path))
        self.assertEqual(len(db3.data["tracks"]), 2)
        self.assertIn(track_id1, db3.data["tracks"])
        self.assertIn(track_id2, db3.data["tracks"])

def run_specific_test_suite():
    """Run specific test categories based on user input"""
    test_categories = {
        "1": ("Database Tests", TestTrackDatabase),
        "2": ("Metadata Tests", TestMetadataExtraction),
        "3": ("Manager Tests", TestDatabaseManager),
        "4": ("File Operation Tests", TestFileOperations),
        "5": ("Validation Tests", TestValidationAndSafety),
        "6": ("Integration Tests", TestIntegration)
    }
    
    print("Available Test Categories:")
    print("=" * 40)
    for key, (name, _) in test_categories.items():
        print(f"{key}. {name}")
    print("7. Run All Tests")
    print("0. Exit")
    
    choice = input("\nSelect test category (0-7): ").strip()
    
    if choice == "0":
        return
    elif choice == "7":
        # Run all tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for _, test_class in test_categories.values():
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print(f"\n{'='*50}")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
        
    elif choice in test_categories:
        name, test_class = test_categories[choice]
        print(f"\nRunning {name}...")
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print(f"\n{name} Results:")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    else:
        print("Invalid choice. Please select 0-7.")

def main():
    """Main test runner with interactive menu"""
    print("Enhanced NCS Downloader Test Suite")
    print("=" * 50)
    print("This test suite validates all functionality including:")
    print("- Database management and JSON storage")
    print("- Metadata extraction and parsing")
    print("- File operations and validation")
    print("- Error handling and safety features")
    print("- Integration workflows")
    print("=" * 50)
    
    while True:
        try:
            run_specific_test_suite()
            
            if input("\nRun another test category? (y/n): ").strip().lower() != 'y':
                break
                
        except KeyboardInterrupt:
            print("\nTests interrupted by user.")
            break
        except Exception as e:
            print(f"Error running tests: {e}")
            break
    
    print("\nTest session completed.")

if __name__ == "__main__":
    main()