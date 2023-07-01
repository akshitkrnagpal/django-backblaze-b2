from typing import Dict
from unittest import mock

import pytest
from b2sdk.account_info.exception import MissingAccountData
from django.core.exceptions import ImproperlyConfigured

from django_backblaze_b2.cache_account_info import DjangoCacheAccountInfo


@pytest.fixture
def allowed() -> Dict:
    return dict(
        bucketId=None,
        bucketName=None,
        capabilities=["readFiles"],
        namePrefix=None,
    )


@pytest.fixture(autouse=True)
def clear_caches():
    from django.core.cache import caches

    for cache in caches.all():
        cache.clear()


def test_helpful_error_on_misconfiguration():
    with pytest.raises(ImproperlyConfigured) as error:
        DjangoCacheAccountInfo("some-invalid-cache-name")

    assert str(error.value) == (
        "Expected to find a cache with name 'some-invalid-cache-name' as per options."
        " The default 'accountInfo' option of this library is with a django cache by the name of 'django-backblaze-b2'"
    )


def test_raises_if_attributes_are_none():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    _ExpectedException = MissingAccountData

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_account_id()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'account_id'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_application_key()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'application_key'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_application_key_id()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'application_key_id'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_account_auth_token()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'auth_token'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_api_url()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'api_url'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_download_url()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'download_url'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_absolute_minimum_part_size()

    assert str(error.value) == _auth_token_msg(
        "Token refresh required to determine value of 'absolute_minimum_part_size'"
    )

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_recommended_part_size()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'recommended_part_size'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_realm()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'realm'")

    with pytest.raises(_ExpectedException) as error:
        cacheAccountInfo.get_allowed()

    assert str(error.value) == _auth_token_msg("Token refresh required to determine value of 'allowed'")

    # notably, no error in default sqlite implementation
    assert cacheAccountInfo.get_s3_api_url() == ""


def test_can_store_and_retrieve_values(allowed: Dict):
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    cacheAccountInfo.set_auth_data(
        "account-id",
        "auth-token",
        "api-url",
        "download-url",
        "recommended-part-size",
        "absolute-minimum-part-size",
        "application-key",
        "realm",
        "http://s3-api-url/",
        allowed,
        "application-key-id",
    )

    assert cacheAccountInfo.get_account_id() == "account-id"
    assert cacheAccountInfo.get_account_auth_token() == "auth-token"
    assert cacheAccountInfo.get_api_url() == "api-url"
    assert cacheAccountInfo.get_download_url() == "download-url"
    assert cacheAccountInfo.get_absolute_minimum_part_size() == "absolute-minimum-part-size"
    assert cacheAccountInfo.get_recommended_part_size() == "recommended-part-size"
    assert cacheAccountInfo.get_application_key() == "application-key"
    assert cacheAccountInfo.get_application_key_id() == "application-key-id"
    assert cacheAccountInfo.get_s3_api_url() == "http://s3-api-url/"
    assert cacheAccountInfo.get_realm() == "realm"
    assert cacheAccountInfo.get_allowed() == allowed


def test_get_bucket_id_when_bucket_name_set():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"
    cacheAccountInfo.save_bucket(bucket)

    bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("some-name")

    assert bucket_id_or_none == "some-id"


def test_get_bucket_id_when_bucket_name_not_set():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")

    bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("some-name")

    assert bucket_id_or_none is None


def test_get_bucket_id_when_bucket_name_deleted():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"
    cacheAccountInfo.save_bucket(bucket)

    cacheAccountInfo.remove_bucket_name("some-name")
    bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("some-name")

    assert bucket_id_or_none is None


def test_can_refresh_entire_bucket_name_cache():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"
    bucket2 = mock.MagicMock()
    bucket2.id_ = "other-id"
    bucket2.name = "other-name"
    bucket3 = mock.MagicMock()
    bucket3.id_ = "another-id"
    bucket3.name = "another-name"
    cacheAccountInfo.save_bucket(bucket)
    cacheAccountInfo.save_bucket(bucket2)
    cacheAccountInfo.save_bucket(bucket3)

    cacheAccountInfo.refresh_entire_bucket_name_cache(
        [("some-name", "some-changed-id"), ("other-changed-name", "other-id"), ("new-bucket", "new-bucket-id")]
    )

    bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("some-name")
    bucket_name_or_none = cacheAccountInfo.get_bucket_name_or_none_from_bucket_id("some-changed-id")
    bucket_name_or_none_from_old_id = cacheAccountInfo.get_bucket_name_or_none_from_bucket_id("some-id")
    bucket2_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("other-changed-name")
    bucket2_id_or_none_from_old_name = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("other-name")
    bucket2_name_or_none = cacheAccountInfo.get_bucket_name_or_none_from_bucket_id("other-id")
    bucket3_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("another-name")
    bucket3_name_or_none = cacheAccountInfo.get_bucket_name_or_none_from_bucket_id("another-id")
    new_bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("new-bucket")
    new_bucket_name_or_none = cacheAccountInfo.get_bucket_name_or_none_from_bucket_id("new-bucket-id")

    assert bucket_id_or_none == "some-changed-id"
    assert bucket_name_or_none == "some-name"
    assert bucket_name_or_none_from_old_id is None
    assert bucket2_id_or_none == "other-id"
    assert bucket2_name_or_none == "other-changed-name"
    assert bucket2_id_or_none_from_old_name is None
    assert bucket3_id_or_none is None
    assert bucket3_name_or_none is None
    assert new_bucket_id_or_none == "new-bucket-id"
    assert new_bucket_name_or_none == "new-bucket"
    for bucket_tuple in [
        ("some-name", "some-changed-id"),
        ("other-changed-name", "other-id"),
        ("new-bucket", "new-bucket-id"),
    ]:
        # assert presence only, list method gives no guarantees on order
        assert bucket_tuple in cacheAccountInfo.list_bucket_names_ids()


def test_can_clear_cache(allowed: Dict):
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    cacheAccountInfo.set_auth_data(
        "account-id",
        "auth-token",
        "api-url",
        "download-url",
        "recommended-part-size",
        "absolute-minimum-part-size",
        "application-key",
        "realm",
        "http://s3-api-url/",
        allowed,
        "application-key-id",
    )
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"
    cacheAccountInfo.save_bucket(bucket)

    cacheAccountInfo.clear()

    bucket_id_or_none = cacheAccountInfo.get_bucket_id_or_none_from_bucket_name("some-name")
    with pytest.raises(MissingAccountData) as error:
        cacheAccountInfo.get_allowed()

    assert bucket_id_or_none is None
    assert error.value is not None


def test_can_perform_operation_after_cache_cleared():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"

    for operation in [
        lambda: cacheAccountInfo.refresh_entire_bucket_name_cache([]),
        lambda: cacheAccountInfo.save_bucket(bucket),
        lambda: cacheAccountInfo.remove_bucket_name("non-extant"),
    ]:
        cacheAccountInfo.clear()

        failure = None
        try:
            operation()
        except Exception as e:
            failure = e
        assert failure is None


def _auth_token_msg(message: str) -> str:
    return str(MissingAccountData(message))


def test_list_bucket_names_ids_when_buckets():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")
    bucket = mock.MagicMock()
    bucket.id_ = "some-id"
    bucket.name = "some-name"
    bucket2 = mock.MagicMock()
    bucket2.id_ = "other-id"
    bucket2.name = "other-name"
    cacheAccountInfo.save_bucket(bucket)
    cacheAccountInfo.save_bucket(bucket2)

    bucket_names_ids = cacheAccountInfo.list_bucket_names_ids()

    assert bucket_names_ids == [("some-name", "some-id"), ("other-name", "other-id")]


def test_list_bucket_names_ids_when_no_buckets():
    cacheAccountInfo = DjangoCacheAccountInfo("test-cache")

    bucket_names_ids = cacheAccountInfo.list_bucket_names_ids()

    assert bucket_names_ids == []
