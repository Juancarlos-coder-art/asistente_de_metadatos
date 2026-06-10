import xml.etree.ElementTree as ET
from typing import Generator
from .base import BaseReader


def _element_to_dict(elem: ET.Element) -> dict:
    """Convert an XML element and its children to a flat dict."""
    record: dict = {}

    # Include element attributes
    for attr_key, attr_val in elem.attrib.items():
        record[attr_key] = attr_val

    # Include text content of the element itself
    text = (elem.text or "").strip()
    if text:
        record["_text"] = text

    # Recurse into children
    for child in elem:
        tag = child.tag
        # Strip namespace if present: {ns}tag -> tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]
        child_dict = _element_to_dict(child)
        if tag in record:
            # Multiple children with same tag: append index suffix
            idx = 1
            while f"{tag}_{idx}" in record:
                idx += 1
            tag = f"{tag}_{idx}"
        if child_dict:
            # Simple leaf (text only, no attributes/children) — use tag directly
            if list(child_dict.keys()) == ["_text"]:
                record[tag] = child_dict["_text"]
            else:
                for k, v in child_dict.items():
                    record[f"{tag}.{k}"] = v
        else:
            child_text = (child.text or "").strip()
            record[tag] = child_text

    return record


class XMLReader(BaseReader):
    def stream_records(self) -> Generator[dict, None, None]:
        """
        Stream XML using iterparse. Assumes the dataset is a list of
        repeated elements under a root. The repeated element type is
        auto-detected as the most frequent direct child tag of root.
        """
        tag_counts: dict[str, int] = {}
        context = ET.iterparse(self.path, events=("start",))

        root = None
        record_tag = None

        for event, elem in context:
            if root is None:
                root = elem
                continue
            # Count direct children of root to find the record element
            if elem in root:
                tag = elem.tag
                if "}" in tag:
                    tag = tag.split("}", 1)[1]
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if len(tag_counts) > 0 and sum(tag_counts.values()) >= 5:
                record_tag = max(tag_counts, key=lambda t: tag_counts[t])
                break

        if record_tag is None and tag_counts:
            record_tag = max(tag_counts, key=lambda t: tag_counts[t])

        if record_tag is None:
            return

        # Second pass: stream record elements
        context = ET.iterparse(self.path, events=("end",))
        for event, elem in context:
            tag = elem.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]
            if tag == record_tag:
                record = _element_to_dict(elem)
                if record:
                    yield record
                elem.clear()  # free memory
