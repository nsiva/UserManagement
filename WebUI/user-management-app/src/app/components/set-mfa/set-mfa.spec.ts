import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SetMfa } from './set-mfa';

describe('SetMfa', () => {
  let component: SetMfa;
  let fixture: ComponentFixture<SetMfa>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SetMfa]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SetMfa);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
