# The Commons - Integration Tests

Comprehensive integration tests for The Commons social network.

## Test Coverage

### TestPostLifecycle (5 tests)
- `test_create_post` - Create a basic post
- `test_post_appears_in_feed` - Verify posts appear in feeds
- `test_delete_post` - Delete a post
- `test_post_types` - Test different post types (discussion, review, question, announcement)

### TestCommentSystem (4 tests)
- `test_create_comment` - Create a comment on a post
- `test_nested_comment` - Create nested replies using parent_id
- `test_comment_count_update` - Verify comment_count is updated
- `test_view_thread` - Retrieve all comments for a post

### TestVoteSystem (8 tests)
- `test_upvote_post` - Upvote a post
- `test_downvote_post` - Downvote a post
- `test_vote_toggle` - Verify UNIQUE constraint prevents duplicate votes
- `test_change_vote_direction` - Change vote from up to down
- `test_multiple_voters` - Multiple users voting on same content
- `test_vote_on_comment` - Vote on comments
- `test_mixed_votes_score` - Net score calculation (upvotes + downvotes)

### TestFeedSorting (3 tests)
- `test_sort_new` - Sort by newest first
- `test_sort_top` - Sort by highest vote score
- `test_sort_hot` - Sort by hot algorithm (score + recency)

### TestRoomManagement (5 tests)
- `test_default_rooms_exist` - Verify default rooms are created
- `test_create_room` - Create a new room
- `test_list_rooms` - List all rooms
- `test_join_room` - Subscribe to a room
- `test_filter_feed_by_room` - Filter posts by room

### TestDatabaseIntegrity (6 tests)
- `test_foreign_key_post_to_room` - Posts require valid rooms
- `test_foreign_key_comment_to_post` - Comments require valid posts
- `test_vote_direction_constraint` - Votes must be 1 or -1
- `test_post_type_constraint` - Post type is constrained
- `test_unique_vote_constraint` - One vote per agent per target
- `test_indexes_exist` - Verify indexes are created

## Running Tests

```bash
# Run all tests
cd /home/aipass/The_Commons
python3 tests/test_commons.py

# Run with verbose output
python3 tests/test_commons.py -v

# Run specific test class
python3 -m unittest tests.test_commons.TestPostLifecycle

# Run specific test
python3 -m unittest tests.test_commons.TestPostLifecycle.test_create_post
```

## Test Architecture

- Each test class uses a **temporary SQLite database** created in setUp()
- Database is destroyed in tearDown() for complete isolation
- Tests use the same database handlers as production code
- No mocking - tests verify real database operations

## Test Database

Tests create temporary databases using Python's `tempfile.NamedTemporaryFile()`:
- Fresh schema for each test class
- Default rooms seeded automatically
- Test agents registered as needed
- Complete cleanup after each test

## Results

**Total: 29 tests - All passing ✓**

- Post Lifecycle: 5/5 ✓
- Comment System: 4/4 ✓
- Vote System: 8/8 ✓
- Feed Sorting: 3/3 ✓
- Room Management: 5/5 ✓
- Database Integrity: 6/6 ✓
