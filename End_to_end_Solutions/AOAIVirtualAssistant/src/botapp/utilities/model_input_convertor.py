class ModelInputConvertor:
    @staticmethod
    def model_input_convertor(transcript):
        input_output_list = list()

        for message in transcript:
            if len(message.utterance) > 0:
                input_output_list.append("user\n" + message.utterance)

        return input_output_list
