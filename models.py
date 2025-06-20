import streamlit as st

class Content:
    """
    Represents a piece of content with an ID, text, status, and author.
    """
    def __init__(self, id: str, text: str, status: str, author: str):
        """
        Initializes a new Content object.

        Args:
            id (str): The unique identifier for the content.
            text (str): The actual content text.
            status (str): The status of the content (e.g., "pending_approval", "approved", "rejected").
            author (str): The author of the content.
        """
        if not isinstance(id, (str, int)):
            raise TypeError("ID must be a string or integer.")
        if not text:
            raise ValueError("Text cannot be empty.")
        if not author:
            raise ValueError("Author cannot be empty.")
        if status not in ["pending_approval", "approved", "rejected", "new"]:
            raise ValueError(f"Invalid status: {status}. Must be one of 'pending_approval', 'approved', 'rejected', 'new'.")

        self._id = str(id)  # Unique identifier for the content
        self._text = text  # The actual content text
        self._status = status  # Status of the content
        self._author = author  # The author of the content

    @property
    def id(self):
        """Gets the ID of the content."""
        return self._id

    @property
    def text(self):
        """Gets the text of the content."""
        return self._text

    @text.setter
    def text(self, new_text: str):
        """Sets the text of the content.

        Args:
            new_text (str): The new text for the content.

        Raises:
            ValueError: If new_text is empty.
        """
        if not new_text:
            raise ValueError("Text cannot be empty.")
        self._text = new_text

    @property
    def status(self):
        """Gets the status of the content."""
        return self._status

    @status.setter
    def status(self, new_status: str):
        """Sets the status of the content.

        Args:
            new_status (str): The new status. Must be one of "pending_approval", "approved", "rejected", "new".

        Raises:
            ValueError: If the new_status is not one of the allowed values.
        """
        if new_status not in ["pending_approval", "approved", "rejected", "new"]:
            raise ValueError(f"Invalid status: {new_status}. Must be one of 'pending_approval', 'approved', 'rejected', 'new'.")
        self._status = new_status

    @property
    def author(self):
        """Gets the author of the content."""
        return self._author

    @author.setter
    def author(self, new_author: str):
        """Sets the author of the content.

        Args:
            new_author (str): The new author of the content.

        Raises:
            ValueError: If new_author is empty.
        """
        if not new_author:
            raise ValueError("Author cannot be empty.")
        self._author = new_author

    def __str__(self):
        """
        Returns a string representation of the Content object.

        Returns:
            str: Formatted string "content - author".
        """
        return f"{self._text} - {self._author}"

    def __add__(self, other):
        """
        Concatenates the text of this Content object with another Content object.
        The new Content object will have the author of the first object and 'new' status.
        The ID of the new object will be a concatenation of the two original IDs.

        Args:
            other (Content): The other Content object to add.

        Returns:
            Content: A new Content object with concatenated text.

        Raises:
            TypeError: If 'other' is not an instance of Content.
        """
        if not isinstance(other, Content):
            raise TypeError("Can only add Content objects")
        new_text = self.text + " " + other.text
        new_id = f"{self.id}_{other.id}"
        return Content(id=new_id, text=new_text, status="new", author=self.author)

    def __len__(self):
        """
        Returns the length of the content text.

        Returns:
            int: The length of the content text.
        """
        return len(self.text)

    def __eq__(self, other):
        """
        Compares two Content objects based on their id.

        Args:
            other (Content): The other Content object to compare with.

        Returns:
            bool: True if the IDs are equal, False otherwise.
        """
        if isinstance(other, Content):
            return self.id == other.id
        return False

    def __repr__(self):
        """
        Returns an unambiguous string representation of the Content object,
        useful for debugging and logging.
        """
        return f"Content(id='{self.id}', text='{self.text[:20]}...', status='{self.status}', author='{self.author}')"
