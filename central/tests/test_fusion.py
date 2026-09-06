from services.fusion import MultiCameraFusion


def test_fusion_matches_by_plate():
    f = MultiCameraFusion()
    a = f.update("BOP-0001-CAM-01", 1, "vehicle", plate="UK07AB1234")
    b = f.update("BOP-0001-CAM-02", 9, "vehicle", plate="UK07AB1234")
    assert a["global_id"] == b["global_id"]
    assert "BOP-0001-CAM-01" in b["cameras_seen"]
    assert "BOP-0001-CAM-02" in b["cameras_seen"]


def test_fusion_matches_by_face_embedding():
    f = MultiCameraFusion(face_threshold=0.48)
    emb = [1.0] + [0.0] * 31
    almost = [0.99] + [0.01] * 31
    a = f.update("BOP-0001-CAM-01", 3, "person", embedding=emb)
    b = f.update("BOP-0002-CAM-01", 7, "person", embedding=almost)
    assert a["global_id"] == b["global_id"]


def test_fusion_new_track_without_identifiers():
    f = MultiCameraFusion()
    a = f.update("CAM-A", 1, "person")
    b = f.update("CAM-B", 2, "person")
    assert a["global_id"] != b["global_id"]
