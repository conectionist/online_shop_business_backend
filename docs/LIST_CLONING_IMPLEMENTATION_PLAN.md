# List Cloning Feature Implementation Plan

## Overview
Simple list cloning feature that duplicates an existing list with all its structure, ordering, and products. The new list will have a different ID but identical content.

## Implementation Steps

### Step 1: Add Clone Endpoint
- [x] Add `POST /liste/{list_id}/clone` endpoint in `app/api/endpoints/lists.py`
- [x] Use existing authentication (admin only)

### Step 2: Implement Clone Service
- [x] Create `clone_list` function in `app/services/list.py`
- [x] Get existing list data from database
- [x] Create new list with same metadata (different ID)
- [x] Copy all category ordering
- [x] Copy all product ordering within categories
- [x] Copy stock quantities

### Step 3: Testing
- [x] Test cloning works correctly
- [x] Verify all relationships are preserved
- [x] Test error handling (invalid list ID, etc.)

### Step 4: Documentation
- [x] Update API docs with new endpoint

## That's it! Simple and straightforward.
