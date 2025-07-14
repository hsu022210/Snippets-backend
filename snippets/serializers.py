from rest_framework import serializers
from snippets.models import Snippet
from django.contrib.auth import get_user_model

User = get_user_model()

# class SnippetSerializer(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source='owner.username')

#     class Meta:
#         model = Snippet
#         fields = ['id', 'title', 'code', 'linenos', 'language', 'style', 'owner']

# class UserSerializer(serializers.ModelSerializer):
#     snippets = serializers.PrimaryKeyRelatedField(many=True, queryset=Snippet.objects.all())

#     class Meta:
#         model = User
#         fields = ['id', 'username', 'snippets']

class SnippetSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    highlight = serializers.HyperlinkedIdentityField(view_name='snippet-highlight', format='html')

    class Meta:
        model = Snippet
        fields = ['url', 'id', 'highlight', 'owner',
                  'title', 'code', 'linenos', 'language', 'style', 'created']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    snippets = serializers.HyperlinkedRelatedField(many=True, view_name='snippet-detail', read_only=True)

    class Meta:
        model = User
        fields = ['url', 'id', 'username', 'snippets']

class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        min_length=1,
        help_text="Sender's full name. Must be provided and cannot be empty.",
        error_messages={
            'blank': 'Name cannot be blank.',
            'required': 'Name is required.',
            'max_length': 'Name cannot exceed 100 characters.'
        }
    )
    email = serializers.EmailField(
        help_text="Sender's email address. Must be a valid email format.",
        error_messages={
            'invalid': 'Enter a valid email address.',
            'required': 'Email is required.',
            'blank': 'Email cannot be blank.'
        }
    )
    subject = serializers.CharField(
        max_length=200,
        min_length=1,
        help_text="Subject line of the contact message. Should be descriptive to help categorize the inquiry.",
        error_messages={
            'blank': 'Subject cannot be blank.',
            'required': 'Subject is required.',
            'max_length': 'Subject cannot exceed 200 characters.'
        }
    )
    message = serializers.CharField(
        min_length=1,
        help_text="The main content of the contact message. Can be any length and will be formatted in the email template.",
        error_messages={
            'blank': 'Message cannot be blank.',
            'required': 'Message is required.'
        }
    )