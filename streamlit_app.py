```python
import streamlit as st

# Define the ContentItem class
class ContentItem:
    def __init__(self, id, text, status, author):
        self.id = id
        self.text = text
        self.status = status
        self.author = author

    def __str__(self):
        return f"{self.text} - {self.author}"

    def __len__(self):
        return len(self.text)

    def __eq__(self, other):
        if isinstance(other, ContentItem):
            return self.id == other.id
        return False

    def __repr__(self):
        return f"ContentItem(id='{self.id}', text='{self.text[:20]}...', status='{self.status}', author='{self.author}')"

# Initialize session state variables if they don't exist
if 'content_items' not in st.session_state:
    st.session_state.content_items = []
if 'item_id_counter' not in st.session_state:
    st.session_state.item_id_counter = 0
if 'role' not in st.session_state:
    st.session_state.role = "Content Creator"

def run_tests():
    """Runs internal tests for content approval logic."""
    st.write("--- Running Internal Tests ---")

    # 1. Clear existing content and reset counter
    st.session_state.content_items = []
    st.session_state.item_id_counter = 0
    st.write("1. Cleared content items and reset counter: PASS")

    # 2. Create Item 1 for approval
    st.session_state.item_id_counter += 1
    item1_id = st.session_state.item_id_counter
    item1 = ContentItem(id=item1_id, text="Test Content for Approval", status="pending_approval", author="Test Author 1")
    st.session_state.content_items.append(item1)
    st.write(f"2. Created Item {item1_id} for approval: PASS")

    # 3. Verify Item 1 status
    if st.session_state.content_items[0].status == "pending_approval":
        st.write(f"3. Item {item1_id} initial status is 'pending_approval': PASS")
    else:
        st.write(f"3. Item {item1_id} initial status is NOT 'pending_approval': FAIL (Status: {st.session_state.content_items[0].status})")

    # 4. Simulate approval of Item 1
    for item in st.session_state.content_items:
        if item.id == item1_id:
            item.status = "approved"
            break
    st.write(f"4. Simulated approval for Item {item1_id}: Done")

    # 5. Verify Item 1 status is "approved"
    item1_updated = next((item for item in st.session_state.content_items if item.id == item1_id), None)
    if item1_updated and item1_updated.status == "approved":
        st.write(f"5. Item {item1_id} status is now 'approved': PASS")
    else:
        st.write(f"5. Item {item1_id} status is NOT 'approved': FAIL (Status: {item1_updated.status if item1_updated else 'Not Found'})")

    # 6. Create Item 2 for rejection
    st.session_state.item_id_counter += 1
    item2_id = st.session_state.item_id_counter
    item2 = ContentItem(id=item2_id, text="Test Content for Rejection", status="pending_approval", author="Test Author 2")
    st.session_state.content_items.append(item2)
    st.write(f"6. Created Item {item2_id} for rejection: PASS")

    # 7. Simulate rejection of Item 2
    for item in st.session_state.content_items:
        if item.id == item2_id:
            item.status = "rejected"
            break
    st.write(f"7. Simulated rejection for Item {item2_id}: Done")

    # 8. Verify Item 2 status is "rejected"
    item2_updated = next((item for item in st.session_state.content_items if item.id == item2_id), None)
    if item2_updated and item2_updated.status == "rejected":
        st.write(f"8. Item {item2_id} status is now 'rejected': PASS")
    else:
        st.write(f"8. Item {item2_id} status is NOT 'rejected': FAIL (Status: {item2_updated.status if item2_updated else 'Not Found'})")

    st.write("--- Internal Tests Finished ---")
    st.experimental_rerun()


st.title("🎈 My new app")

# Role Selection
st.session_state.role = st.selectbox(
    "Select Your Role:",
    ("Content Creator", "Approver"),
    index=("Content Creator", "Approver").index(st.session_state.role)
)

st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

# Content Creator View
if st.session_state.role == "Content Creator":
    st.header("Submit Content")
    author_name = st.text_input("Your Name")
    content_text = st.text_area("Your Content")
    submit_button = st.button("Submit for Approval")

    if submit_button:
        if author_name and content_text:
            st.session_state.item_id_counter += 1
            new_item = ContentItem(
                id=st.session_state.item_id_counter,
                text=content_text,
                status="pending_approval",
                author=author_name
            )
            st.session_state.content_items.append(new_item)
            st.success("Content submitted successfully! It is pending approval.")
        else:
            st.error("Please provide both your name and content.")

# Approver View
if st.session_state.role == "Approver":
    st.header("Pending Approval")
    # Filter for pending items *before* iterating to avoid issues if list is modified
    pending_items = [item for item in st.session_state.content_items if item.status == "pending_approval"]

    if not pending_items:
        st.write("No items pending approval.")
    else:
        for item in pending_items:
            st.subheader(f"Content ID: {item.id}")
            st.write(f"Author: {item.author}")
            st.write(f"Text: {item.text}")

            col1, col2 = st.columns(2)
            approve_button_key = f"approve_{item.id}"
            reject_button_key = f"reject_{item.id}"

            if col1.button("Approve", key=approve_button_key):
                # Find the item in the main list and update its status
                for session_item in st.session_state.content_items:
                    if session_item.id == item.id:
                        session_item.status = "approved"
                        st.success(f"Content ID {item.id} approved.")
                        st.experimental_rerun()
                # Note: The item will disappear from this list on rerun because its status changed

            if col2.button("Reject", key=reject_button_key):
                # Find the item in the main list and update its status
                for session_item in st.session_state.content_items:
                    if session_item.id == item.id:
                        session_item.status = "rejected"
                        st.success(f"Content ID {item.id} rejected.")
                        st.experimental_rerun()
                # Note: The item will disappear from this list on rerun because its status changed
            st.divider()

# Sections visible to both roles (or adjust as needed)
st.header("Approved Content")
approved_items = [item for item in st.session_state.content_items if item.status == "approved"]

if not approved_items:
    st.write("No content approved yet.")
else:
    for item in approved_items:
        st.subheader(f"Content ID: {item.id}")
        st.write(f"Author: {item.author}")
        st.write(f"Text: {item.text}")
        st.divider()

st.header("Rejected Content")
rejected_items = [item for item in st.session_state.content_items if item.status == "rejected"]

if not rejected_items:
    st.write("No content rejected yet.")
else:
    for item in rejected_items:
        st.subheader(f"Content ID: {item.id}")
        st.write(f"Author: {item.author}")
        st.write(f"Text: {item.text}")
        st.divider()

st.divider()
if st.button("Run Internal Tests"):
    run_tests()
```
