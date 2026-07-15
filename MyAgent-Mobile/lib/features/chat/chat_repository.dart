import '../../core/network/api_client.dart';
import '../../shared/models/models.dart';

class ChatRepository {
  const ChatRepository(this._api);

  final ApiClient _api;

  Future<List<ConversationModel>> conversations() async {
    final response = await _api.dio.get<List<dynamic>>('/conversations');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(ConversationModel.fromJson)
        .toList();
  }

  Future<List<ChatMessageModel>> messages(String conversationId) async {
    final response = await _api.dio.get<List<dynamic>>(
      '/conversations/$conversationId/messages',
    );
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(ChatMessageModel.fromJson)
        .toList();
  }

  Future<ChatReply> send({
    required String message,
    String? conversationId,
    String? provider,
  }) async {
    final response = await _api.dio.post<Map<String, dynamic>>(
      '/chat',
      data: {
        'message': message,
        if (conversationId != null) 'conversation_id': conversationId,
        if (provider != null) 'provider': provider,
      },
    );
    return ChatReply.fromJson(response.data!);
  }

  Future<List<ProviderModel>> providers() async {
    final response = await _api.dio.get<List<dynamic>>('/providers');
    return response.data!
        .cast<Map<String, dynamic>>()
        .map(ProviderModel.fromJson)
        .toList();
  }

  Future<void> deleteConversation(String conversationId) =>
      _api.dio.delete<void>('/conversations/$conversationId');
}
