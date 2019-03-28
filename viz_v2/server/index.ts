import { Server } from "./server";
import * as configFile from './config';
const config = configFile.Config;

const server = new Server(config);
server.start()
    .then(() => {
        console.log(`Server started with at port ${config.port}`);
    })
    .catch((e: Error) => {
        console.error(`Server failed to start at port ${config.port}`);
        console.error(e);
        process.exit(1);
    });