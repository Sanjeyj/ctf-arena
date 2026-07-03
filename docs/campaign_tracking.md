# Threat Campaign Timelines & Tracking

This guide details campaign tracking functionalities, mapping actor relationships to sectors and operational timelines.

---

## 1. Campaign Tracking parameters
Campaigns are tracked using the following entities:
- **Campaign ID & Name**: System designation (e.g. Operation Windigo).
- **Actor Association**: Mapped Threat Actor group ID.
- **Sectors Affected**: Target industries (e.g. Healthcare, Energy).
- **Malware Families Used**: Malware signatures detected in the campaign stream.
- **Operational Timelines**: Start and End dates of active operations.

---

## 2. Interactive Timeline Reconstruction
The platform aggregates active campaign entries into a sequential timeline stream. This allows analysts to visualize:
1. Multi-stage attack progressions chronologically.
2. Changes in targeted industry sectors over time.
3. Evolutionary modifications in deployed malware sets.
4. TTP shifts matching technique mappings.
