
import * as fs from "fs";

import { Server } from "./server";

const args = process.argv.slice(2);

const config = JSON.parse(fs.readFileSync(args[0], "utf8"));

const server = new Server(config);
server.start()
    .then(() => {
        console.log(`Server started on port: ${server.port}  width config ${args[0]}`);
    })
    .catch((e: Error) => {
        console.error(`Server failed to start on port: ${server.port}  width config ${args[0]}`);
        console.error(e);
        process.exit(1);
    });
