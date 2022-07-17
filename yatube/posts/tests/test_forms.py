import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    def test_create_post_with_image(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Другой тестовый текст',
            'image': uploaded
        }

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Другой тестовый текст',
                group=None,
                author=self.user,
                image='posts/small.gif').exists())

    def test_edit_post(self):
        """Валидная форма сохраняет исправленный пост"""
        posts_count = Post.objects.count()
        post_pk = PostPagesTest.post.pk
        form_data = {
            'text': 'Исправленный текст',
        }

        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'pk': post_pk}),
            data=form_data,
            follow=True
        )

        self.assertTrue(
            (Post.objects.filter(
                pk=post_pk,
                text='Исправленный текст',
                author=self.user).exists()))
        self.assertEqual(Post.objects.count(), posts_count)

    def add_comment(self):
        """После заполнения формы комментарий добавляется на страницу"""
        comments_count = Comment.objects.count()
        post_pk = self.post.pk
        form_data = {'text': 'Другой тестовый комментарий'}

        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'pk': post_pk}),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='Другой тестовый комментарий').exists())
