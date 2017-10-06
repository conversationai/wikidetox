import { Crowd9DemoPage } from './app.po';

describe('crowd9-demo App', () => {
  let page: Crowd9DemoPage;

  beforeEach(() => {
    page = new Crowd9DemoPage();
  });

  it('should display welcome message', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('Welcome to app!');
  });
});
