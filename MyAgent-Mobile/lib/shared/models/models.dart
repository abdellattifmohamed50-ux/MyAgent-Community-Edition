class UserModel {
  const UserModel({
    required this.id,
    required this.email,
    required this.displayName,
    required this.role,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
    id: json['id'] as String,
    email: json['email'] as String,
    displayName: json['display_name'] as String,
    role: json['role'] as String,
  );

  final String id;
  final String email;
  final String displayName;
  final String role;
}

class TokenBundle {
  const TokenBundle({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  factory TokenBundle.fromJson(Map<String, dynamic> json) => TokenBundle(
    accessToken: json['access_token'] as String,
    refreshToken: json['refresh_token'] as String,
    user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
  );

  final String accessToken;
  final String refreshToken;
  final UserModel user;
}

class ConversationModel {
  const ConversationModel({
    required this.id,
    required this.title,
    this.provider,
    this.projectId,
  });

  factory ConversationModel.fromJson(Map<String, dynamic> json) =>
      ConversationModel(
        id: json['id'] as String,
        title: json['title'] as String,
        provider: json['provider'] as String?,
        projectId: json['project_id'] as String?,
      );

  final String id;
  final String title;
  final String? provider;
  final String? projectId;
}

class ChatMessageModel {
  const ChatMessageModel({
    required this.id,
    required this.role,
    required this.content,
    this.provider,
  });

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) =>
      ChatMessageModel(
        id: json['id'] as String,
        role: json['role'] as String,
        content: json['content'] as String,
        provider: json['provider'] as String?,
      );

  final String id;
  final String role;
  final String content;
  final String? provider;
}

class ChatReply {
  const ChatReply({
    required this.conversationId,
    required this.message,
    required this.provider,
    required this.model,
  });

  factory ChatReply.fromJson(Map<String, dynamic> json) => ChatReply(
    conversationId: json['conversation_id'] as String,
    message: json['message'] as String,
    provider: json['provider'] as String,
    model: json['model'] as String,
  );

  final String conversationId;
  final String message;
  final String provider;
  final String model;
}

class ProviderModel {
  const ProviderModel({
    required this.name,
    required this.model,
    required this.configured,
    required this.healthy,
  });

  factory ProviderModel.fromJson(Map<String, dynamic> json) => ProviderModel(
    name: json['name'] as String,
    model: json['model'] as String,
    configured: json['configured'] as bool,
    healthy: json['healthy'] as bool,
  );

  final String name;
  final String model;
  final bool configured;
  final bool healthy;
}
