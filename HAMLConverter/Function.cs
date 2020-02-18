using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Amazon;
using Amazon.Lambda.Core;
using Amazon.Lambda.RuntimeSupport;
using Amazon.Lambda.S3Events;
using Amazon.Lambda.Serialization.Json;
using Amazon.S3;
using Amazon.S3.Model;
using Amazon.S3.Util;

// Assembly attribute to enable the Lambda function's JSON input to be converted into a .NET class.
[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.Json.JsonSerializer))]

namespace HAMLConverter
{
    public class Function
    {
        private static IAmazonS3 s3Client;

        /// <summary>
        /// The main entry point for the custom runtime.
        /// </summary>
        /// <param name="args"></param>
        private static async Task Main(string[] args)
        {
            s3Client = new AmazonS3Client();

            Func<S3Event, ILambdaContext, Task<string>> func = FunctionHandler;
            using (var handlerWrapper = HandlerWrapper.GetHandlerWrapper(func, new JsonSerializer()))
            using (var bootstrap = new LambdaBootstrap(handlerWrapper))
            {
                await bootstrap.RunAsync();
            }
        }

        /// <summary>
        /// A simple function that takes a string and does a ToUpper
        ///
        /// To use this handler to respond to an AWS event, reference the appropriate package from 
        /// https://github.com/aws/aws-lambda-dotnet#events
        /// and change the string input parameter to the desired event type.
        /// </summary>
        /// <param name="input"></param>
        /// <param name="context"></param>
        /// <returns></returns>
        public static async Task<string> FunctionHandler(S3Event evnt, ILambdaContext context)
        {
            var s3Event = evnt.Records?[0].S3;
            if (s3Event == null)
            {
                return null;
            }

            try
            {
                var response = await s3Client.GetObjectAsync(s3Event.Bucket.Name, s3Event.Object.Key);
                StreamReader reader = new StreamReader(response.ResponseStream);

                String content = reader.ReadToEnd();
                var converter = new Converter(Encoding.ASCII.GetBytes(content));
                converter.DetermineManufacturer();

                if (converter.Manufacturer == "OneLambda")
                {
                    converter.ProcessOneLambda("asdf");
                }
                else if (converter.Manufacturer == "Immucor")
                {
                    converter.ProcessImmucor("asdf");
                }

                context.Logger.LogLine(Encoding.UTF8.GetString(converter.XmlFile));

                var putRequest = new PutObjectRequest
                {
                    BucketName = s3Event.Bucket.Name,
                    Key = s3Event.Object.Key + ".haml",
                    ContentBody = Encoding.UTF8.GetString(converter.XmlFile)
                };
                _ = s3Client.PutObjectAsync(putRequest);
                return response.Headers.ContentType;
            }
            catch (Exception e)
            {
                context.Logger.LogLine($"Error getting object {s3Event.Object.Key} from bucket {s3Event.Bucket.Name}. Make sure they exist and your bucket is in the same region as this function.");
                context.Logger.LogLine(e.Message);
                context.Logger.LogLine(e.StackTrace);
                throw;
            }
        }

    }
}
