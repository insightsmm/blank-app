import unittest
from models import Content

class TestContent(unittest.TestCase):

    def test_content_creation_valid(self):
        """Test successful creation of a Content object."""
        content = Content(id="1", text="Hello World", status="pending_approval", author="John Doe")
        self.assertEqual(content.id, "1")
        self.assertEqual(content.text, "Hello World")
        self.assertEqual(content.status, "pending_approval")
        self.assertEqual(content.author, "John Doe")

    def test_content_creation_valid_id_types(self):
        """Test Content creation with valid id types (str and int)."""
        content_str_id = Content(id="123", text="Some text", status="approved", author="Jane Doe")
        self.assertEqual(content_str_id.id, "123")
        content_int_id = Content(id=123, text="Some text", status="approved", author="Jane Doe")
        self.assertEqual(content_int_id.id, "123") # Should be converted to string

    def test_content_creation_empty_text(self):
        """Test Content creation with empty text."""
        with self.assertRaises(ValueError):
            Content(id="2", text="", status="approved", author="Jane Doe")

    def test_content_creation_empty_author(self):
        """Test Content creation with empty author."""
        with self.assertRaises(ValueError):
            Content(id="3", text="Some text", status="approved", author="")

    def test_content_creation_invalid_status(self):
        """Test Content creation with an invalid status."""
        with self.assertRaises(ValueError):
            Content(id="4", text="Some text", status="unknown", author="Jane Doe")

    def test_str_representation(self):
        """Test the __str__ method for correct formatting."""
        content = Content(id="5", text="Test Content", status="approved", author="Test Author")
        self.assertEqual(str(content), "Test Content - Test Author")

    def test_len_method(self):
        """Test the __len__ method returns the length of the text."""
        content = Content(id="6", text="Hello", status="approved", author="Test Author")
        self.assertEqual(len(content), 5)

    def test_add_method(self):
        """Test adding two Content objects."""
        content1 = Content(id="c1", text="Hello", status="approved", author="Author1")
        content2 = Content(id="c2", text="World", status="pending_approval", author="Author2")
        combined_content = content1 + content2
        self.assertEqual(combined_content.text, "Hello World")
        self.assertEqual(combined_content.author, "Author1") # Author should be from the first operand
        self.assertEqual(combined_content.status, "new")
        self.assertEqual(combined_content.id, "c1_c2")

    def test_add_method_type_error(self):
        """Test adding a Content object with a non-Content object."""
        content = Content(id="7", text="Test", status="approved", author="Author")
        with self.assertRaises(TypeError):
            _ = content + "string"

    def test_eq_method(self):
        """Test the __eq__ method for comparing Content objects."""
        content1 = Content(id="8", text="Text1", status="approved", author="Author1")
        content2 = Content(id="8", text="Text2", status="pending_approval", author="Author2")
        content3 = Content(id="9", text="Text1", status="approved", author="Author1")
        self.assertEqual(content1, content2)  # Same ID
        self.assertNotEqual(content1, content3) # Different ID
        self.assertNotEqual(content1, "not a content object") # Different type

    def test_id_property(self):
        """Test the id property (getter and read-only)."""
        content = Content(id="10", text="Test", status="approved", author="Author")
        self.assertEqual(content.id, "10")
        with self.assertRaises(AttributeError):
            content.id = "20"  # Should fail as id is read-only

    def test_text_property(self):
        """Test the text property (getter and setter)."""
        content = Content(id="11", text="Initial Text", status="approved", author="Author")
        self.assertEqual(content.text, "Initial Text")
        content.text = "Updated Text"
        self.assertEqual(content.text, "Updated Text")
        with self.assertRaises(ValueError):
            content.text = ""  # Should fail due to empty string

    def test_status_property(self):
        """Test the status property (getter and setter)."""
        content = Content(id="12", text="Test", status="pending_approval", author="Author")
        self.assertEqual(content.status, "pending_approval")

        valid_statuses = ["approved", "rejected", "pending_approval"]
        for status in valid_statuses:
            content.status = status
            self.assertEqual(content.status, status)

        with self.assertRaises(ValueError):
            content.status = "invalid_status"

    def test_author_property(self):
        """Test the author property (getter and setter)."""
        content = Content(id="13", text="Test", status="approved", author="Initial Author")
        self.assertEqual(content.author, "Initial Author")
        content.author = "New Author"
        self.assertEqual(content.author, "New Author")
        with self.assertRaises(ValueError):
            content.author = ""  # Should fail due to empty string

    def test_repr_method(self):
        """Test the __repr__ method for a developer-friendly representation."""
        content = Content(id="14", text="This is a longer text for repr.", status="approved", author="Repr Author")
        expected_repr = "Content(id='14', text='This is a longer tex...', status='approved', author='Repr Author')"
        self.assertEqual(repr(content), expected_repr)

if __name__ == '__main__':
    unittest.main()
